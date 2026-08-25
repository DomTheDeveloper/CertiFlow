from __future__ import annotations

"""Conservative normalization for a documented SQL SELECT fragment."""
import re
from .model import IRNode

class SQLNormalizationError(ValueError): pass
_TOKEN = re.compile(r"\s*(?:(?P<ident>[A-Za-z_][A-Za-z0-9_$]*(?:\.[A-Za-z_][A-Za-z0-9_$]*|\.\*)*)|(?P<number>\d+(?:\.\d+)?)|(?P<string>'(?:''|[^'])*')|(?P<op><=|>=|<>|!=|=|<|>)|(?P<comma>,)|(?P<star>\*)|(?P<lpar>\()|(?P<rpar>\))|(?P<other>\S))")

def strip_sql_comments(sql: str) -> str: return "\n".join(line.split("--",1)[0] for line in sql.splitlines())
def _tokens(sql: str) -> list[str]:
    sql=strip_sql_comments(sql)
    if ";" in sql.strip().rstrip(";"): raise SQLNormalizationError("multiple SQL statements are not supported")
    sql=sql.strip().rstrip(";").strip(); out=[]; pos=0
    while pos < len(sql):
        m=_TOKEN.match(sql,pos)
        if not m: raise SQLNormalizationError(f"cannot tokenize SQL near offset {pos}")
        token=m.group(0).strip()
        if m.lastgroup=="other": raise SQLNormalizationError(f"unsupported token: {token}")
        out.append(token); pos=m.end()
    return out

def _upper(t:str)->str:return t.upper()
def _split_top_level(tokens:list[str],delimiter:str=",")->list[list[str]]:
    result=[]; current=[]; depth=0
    for token in tokens:
        if token=="(": depth+=1
        elif token==")":
            depth-=1
            if depth<0: raise SQLNormalizationError("unbalanced parentheses")
        if token==delimiter and depth==0: result.append(current); current=[]
        else: current.append(token)
    if depth!=0: raise SQLNormalizationError("unbalanced parentheses")
    if current: result.append(current)
    return result

def _find_keyword(tokens,keyword,start=0):
    depth=0
    for i in range(start,len(tokens)):
        if tokens[i]=="(":depth+=1
        elif tokens[i]==")":depth-=1
        elif depth==0 and _upper(tokens[i])==keyword:return i
    return None

def _find_two_word(tokens,a,b,start=0):
    depth=0
    for i in range(start,len(tokens)-1):
        if tokens[i]=="(":depth+=1
        elif tokens[i]==")":depth-=1
        elif depth==0 and _upper(tokens[i])==a and _upper(tokens[i+1])==b:return i
    return None

def _alias_split(expr):
    upper=[_upper(t) for t in expr]
    if "AS" in upper:
        idx=len(upper)-1-upper[::-1].index("AS")
        if idx+1>=len(expr):raise SQLNormalizationError("AS requires an alias")
        return expr[:idx],expr[idx+1]
    if len(expr)==2 and expr[0] not in {"*","("}:return expr[:1],expr[1]
    return expr,None

def _base_column(expr):
    body,_=_alias_split(expr)
    if len(body)!=1 or "(" in body or ")" in body:return None
    token=body[0]
    if token=="*" or token.startswith("'") or token[0].isdigit():return None
    return token.split(".")[-1]
def _output_name(expr,ordinal):
    body,alias=_alias_split(expr)
    if alias:return alias
    if len(body)==1 and body[0]!="*":return body[0].split(".")[-1]
    return f"__expr_{ordinal}"

def normalize_select(sql:str,*,name:str="query",engine:str="sql")->list[IRNode]:
    tokens=_tokens(sql)
    if not tokens or _upper(tokens[0])!="SELECT":raise SQLNormalizationError("only SELECT statements are supported")
    for keyword in ("UNION","INTERSECT","EXCEPT"):
        if _find_keyword(tokens,keyword,1) is not None:raise SQLNormalizationError(f"{keyword} is outside the certifiable fragment")
    from_idx=_find_keyword(tokens,"FROM",1)
    if from_idx is None:raise SQLNormalizationError("SELECT requires FROM")
    where_idx=_find_keyword(tokens,"WHERE",from_idx+1); group_idx=_find_two_word(tokens,"GROUP","BY",from_idx+1)
    order_idx=_find_two_word(tokens,"ORDER","BY",from_idx+1); having_idx=_find_keyword(tokens,"HAVING",from_idx+1); limit_idx=_find_keyword(tokens,"LIMIT",from_idx+1)
    if order_idx is not None:raise SQLNormalizationError("ORDER BY is outside the certifiable fragment")
    if having_idx is not None:raise SQLNormalizationError("HAVING is outside the certifiable fragment")
    if limit_idx is not None:raise SQLNormalizationError("LIMIT is outside the certifiable fragment")
    stops=[x for x in (where_idx,group_idx,len(tokens)) if x is not None]; from_end=min(x for x in stops if x>from_idx); ft=tokens[from_idx+1:from_end]
    if not ft:raise SQLNormalizationError("missing FROM relation")
    nodes=[]; pos=0; base=ft[pos]; pos+=1
    if base=="(":raise SQLNormalizationError("subqueries in FROM are not supported")
    if pos<len(ft) and _upper(ft[pos]) not in {"JOIN","LEFT","INNER"}:pos+=1
    nodes.append(IRNode("Scan",base,{},engine=engine,source_ref=base)); current=base; join_no=0
    while pos<len(ft):
        jt="inner"
        if _upper(ft[pos]) in {"LEFT","INNER"}:jt=_upper(ft[pos]).lower();pos+=1
        if pos>=len(ft) or _upper(ft[pos])!="JOIN":raise SQLNormalizationError("expected JOIN")
        pos+=1; rel=ft[pos];pos+=1
        if pos<len(ft) and _upper(ft[pos])!="ON":pos+=1
        nodes.append(IRNode("Scan",rel,{},engine=engine,source_ref=rel))
        if pos>=len(ft) or _upper(ft[pos])!="ON":raise SQLNormalizationError("JOIN requires ON")
        pos+=1
        if pos+2>=len(ft) or ft[pos+1]!="=":raise SQLNormalizationError("only single equi-joins are supported")
        left,right=ft[pos],ft[pos+2];pos+=3
        if pos<len(ft) and _upper(ft[pos]) in {"AND","OR"}:raise SQLNormalizationError("multi-predicate joins are not yet supported")
        join_no+=1;jname=f"{name}__join{join_no}";nodes.append(IRNode("Join",jname,{"join_type":jt,"equi":((left.split(".")[-1],right.split(".")[-1]),)},(current,rel),engine=engine,source_ref=sql));current=jname
    if where_idx is not None:
        end=group_idx if group_idx is not None else len(tokens); predicate=" ".join(tokens[where_idx+1:end]);fname=f"{name}__filter";nodes.append(IRNode("Filter",fname,{"predicate":predicate},(current,),engine=engine,source_ref=sql));current=fname
    expressions=_split_top_level(tokens[1:from_idx])
    if group_idx is not None:
        group_by=tuple(" ".join(e).split(".")[-1] for e in _split_top_level(tokens[group_idx+2:]));aggregates={};passthrough={};computed={}
        for ordinal,expr in enumerate(expressions):
            if expr==["*"]:continue
            text=" ".join(expr);out=_output_name(expr,ordinal);src=_base_column(expr)
            if src is not None:passthrough[out]=src
            elif "(" in expr:aggregates[out]=text
            else:computed[out]=text
        gname=f"{name}__group";nodes.append(IRNode("Group",gname,{"group_by":group_by,"aggregates":aggregates,"passthrough":passthrough,"computed":computed},(current,),engine=engine,source_ref=sql));current=gname
    else:
        mapping={};computed={};wildcard=False
        for ordinal,expr in enumerate(expressions):
            if expr==["*"] or (len(expr)==1 and expr[0].endswith(".*")):wildcard=True;continue
            src=_base_column(expr);out=_output_name(expr,ordinal)
            if src is None:computed[out]=" ".join(expr)
            else:mapping[out]=src
        if mapping or computed:
            nodes.append(IRNode("Project",name,{"mapping":mapping,"computed":computed,"wildcard":wildcard},(current,),engine=engine,source_ref=sql))
    return nodes
