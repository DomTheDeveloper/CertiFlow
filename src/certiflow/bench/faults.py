from __future__ import annotations
from dataclasses import replace
from ..model import IRNode

def mutate_join_key(node: IRNode) -> IRNode:
    if node.op != "Join": return node
    equi=tuple(tuple(x) for x in node.args.get("equi",()))
    if not equi: return node
    bad=list(equi); bad[0]=(bad[0][0],"__wrong_key__"); args=dict(node.args); args["equi"]=tuple(bad); return replace(node,args=args)
def mutate_group_grain(node: IRNode) -> IRNode:
    if node.op != "Group": return node
    args=dict(node.args); args["group_by"]=tuple(args.get("group_by",()))+("__extra_grain__",); return replace(node,args=args)
def mutate_projection(node: IRNode) -> IRNode:
    if node.op != "Project": return node
    args=dict(node.args); mapping=dict(args.get("mapping",{}))
    if mapping: mapping[next(iter(mapping))]="__wrong_source__"
    args["mapping"]=mapping; return replace(node,args=args)
def mutate_schema(node: IRNode) -> IRNode:
    args=dict(node.args); schema=dict(args.get("schema",{}))
    if schema: schema[next(iter(schema))]="__wrong_type__"
    args["schema"]=schema; return replace(node,args=args)
def mutate_restricted_flow(node: IRNode) -> IRNode:
    args=dict(node.args); lineage={k:list(v) for k,v in args.get("lineage",{}).items()}
    if lineage:
        first=next(iter(lineage)); lineage[first]=list(lineage[first])+["ssn"]
    else: lineage={"public":["ssn"]}
    args["lineage"]=lineage; return replace(node,args=args)
MUTATORS={"join_key":mutate_join_key,"group_grain":mutate_group_grain,"projection":mutate_projection,"schema":mutate_schema,"restricted_flow":mutate_restricted_flow}
