from __future__ import annotations

"""dbt-aware preprocessing and CTE normalization.

This module understands only enough Jinja to make relational structure explicit:
`ref()` and `source()` become relation identifiers. Other Jinja expressions are
replaced by opaque expression calls so that CertiFlow can preserve their output
columns without assigning them semantics.
"""

from dataclasses import dataclass
import re

from .graph import PipelineGraph
from .model import IRNode
from .sqlnorm import SQLNormalizationError, normalize_select, strip_sql_comments

_REF = re.compile(r"\{\{\s*ref\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}")
_SOURCE = re.compile(r"\{\{\s*source\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}")
_CONFIG = re.compile(r"\{\{\s*config\(.*?\)\s*\}\}", re.DOTALL | re.IGNORECASE)
_JINJA = re.compile(r"\{\{.*?\}\}", re.DOTALL)

class DbtSQLNormalizationError(SQLNormalizationError):
    pass

@dataclass
class DbtModelNormalization:
    model_name: str
    graph: PipelineGraph
    ctes: tuple[str, ...]
    opaque_expressions: int
    opaque_relations: int

def preprocess_dbt_sql(sql: str) -> tuple[str, int]:
    sql = strip_sql_comments(sql)
    sql = _CONFIG.sub("", sql)
    sql = _REF.sub(lambda m: m.group(1), sql)
    sql = _SOURCE.sub(lambda m: f"{m.group(1)}__{m.group(2)}", sql)
    counter = 0
    def opaque(_: re.Match[str]) -> str:
        nonlocal counter
        counter += 1
        return f"DBT_EXPR_{counter}()"
    sql = _JINJA.sub(opaque, sql)
    return sql, counter

def _skip_ws(sql: str, pos: int) -> int:
    while pos < len(sql) and sql[pos].isspace(): pos += 1
    return pos

def _read_ident(sql: str, pos: int) -> tuple[str, int]:
    m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", sql[pos:])
    if not m: raise DbtSQLNormalizationError(f"expected CTE identifier near offset {pos}")
    return m.group(0), pos + len(m.group(0))

def _matching_paren(sql: str, pos: int) -> int:
    if pos >= len(sql) or sql[pos] != "(": raise DbtSQLNormalizationError("expected opening parenthesis")
    depth = 0; in_string = False; i = pos
    while i < len(sql):
        ch = sql[i]
        if ch == "'":
            if in_string and i + 1 < len(sql) and sql[i + 1] == "'": i += 2; continue
            in_string = not in_string
        elif not in_string:
            if ch == "(": depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0: return i
        i += 1
    raise DbtSQLNormalizationError("unbalanced CTE parentheses")

def split_ctes(sql: str) -> tuple[list[tuple[str, str]], str]:
    stripped = sql.strip(); m = re.match(r"(?is)^with\b", stripped)
    if not m: return [], stripped
    pos = m.end(); ctes: list[tuple[str, str]] = []
    while True:
        pos = _skip_ws(stripped, pos); name, pos = _read_ident(stripped, pos); pos = _skip_ws(stripped, pos)
        if stripped[pos:pos + 2].upper() != "AS": raise DbtSQLNormalizationError(f"CTE {name} is missing AS")
        pos += 2; pos = _skip_ws(stripped, pos); end = _matching_paren(stripped, pos)
        ctes.append((name, stripped[pos + 1:end].strip())); pos = _skip_ws(stripped, end + 1)
        if pos < len(stripped) and stripped[pos] == ",": pos += 1; continue
        final = stripped[pos:].strip()
        if not final: raise DbtSQLNormalizationError("WITH clause is missing final SELECT")
        return ctes, final

def normalize_dbt_model(sql: str, *, model_name: str, engine: str = "dbt") -> DbtModelNormalization:
    preprocessed, opaque_count = preprocess_dbt_sql(sql)
    ctes, final_sql = split_ctes(preprocessed)
    by_name: dict[str, IRNode] = {}; cte_outputs: dict[str, str] = {}; opaque_relations = 0
    def add_node(node: IRNode) -> None:
        previous = by_name.get(node.name)
        if previous is None: by_name[node.name] = node
        elif previous.hash != node.hash: raise DbtSQLNormalizationError(f"conflicting normalized node identity: {node.name}")
    def rewrite_inputs(node: IRNode) -> IRNode:
        from dataclasses import replace
        inputs = tuple(cte_outputs.get(inp, inp) for inp in node.inputs)
        return node if inputs == node.inputs else replace(node, inputs=inputs)
    def add_query(query: str, output_name: str) -> None:
        nonlocal opaque_relations
        if not query.lstrip().upper().startswith("SELECT"):
            add_node(IRNode("Opaque", output_name, {"reason": "non-select relation expression", "expression": query}, (), engine=engine, source_ref=query))
            opaque_relations += 1; return
        normalized = normalize_select(query, name=output_name, engine=engine)
        for raw_node in normalized:
            if raw_node.op == "Scan" and raw_node.name in cte_outputs: continue
            add_node(rewrite_inputs(raw_node))
        raw_output = normalized[-1].name if normalized else ""; output = cte_outputs.get(raw_output, raw_output)
        if raw_output != output_name:
            add_node(IRNode("Alias", output_name, {}, (output,), engine=engine, source_ref=query))
    for cte_name, body in ctes:
        internal = f"{model_name}__cte__{cte_name}"; add_query(body, internal); cte_outputs[cte_name] = internal
    add_query(final_sql, model_name)
    graph = PipelineGraph.from_nodes(by_name.values())
    return DbtModelNormalization(model_name, graph, tuple(name for name, _ in ctes), opaque_count, opaque_relations)
