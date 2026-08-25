from __future__ import annotations
from typing import Callable, Dict, Iterable
from .model import Certificate, CheckResult, Fact, IRNode, Verdict
from .store import FactStore

Rule = Callable[[IRNode, Certificate, FactStore], CheckResult]

class RuleRegistry:
    def __init__(self) -> None:
        self._rules: Dict[str, Rule] = {}
    def register(self, name: str, fn: Rule) -> None:
        if name in self._rules: raise ValueError(f"rule already registered: {name}")
        self._rules[name] = fn
    def get(self, name: str) -> Rule | None: return self._rules.get(name)
    def names(self) -> tuple[str, ...]: return tuple(sorted(self._rules))

def _accept(rule, cert, claims): return CheckResult(Verdict.ACCEPT, list(claims), rule=rule, certificate_id=cert.id)
def _reject(rule, cert, reason): return CheckResult(Verdict.REJECT, reason=reason, rule=rule, certificate_id=cert.id)
def _unknown(rule, cert, reason): return CheckResult(Verdict.UNKNOWN, reason=reason, rule=rule, certificate_id=cert.id)

def project_key(node, cert, store):
    rule="project_key"
    if node.op != "Project": return _reject(rule, cert, "operator is not Project")
    mapping=node.args.get("mapping", {}); src_key=tuple(cert.witness.get("source_key", ())); out_key=tuple(cert.witness.get("output_key", ()))
    if not src_key or len(src_key)!=len(out_key): return _reject(rule, cert, "malformed key witness")
    if any(mapping.get(out)!=src for src,out in zip(src_key,out_key)): return _reject(rule, cert, "projection does not preserve key mapping")
    return _accept(rule, cert, [Fact.make("Key", node.name, {"columns": out_key}, cert.assumptions)])

def join_fanout(node, cert, store):
    rule="join_fanout"
    if node.op != "Join": return _reject(rule, cert, "operator is not Join")
    if node.args.get("join_type","inner") not in {"inner","left"}: return _unknown(rule, cert, "join type is outside the certified fragment")
    left_col=cert.witness.get("left_col"); right_col=cert.witness.get("right_col"); right_rel=cert.witness.get("right_relation")
    if (left_col,right_col) not in tuple(tuple(x) for x in node.args.get("equi",())): return _reject(rule, cert, "witness does not match normalized equality predicate")
    keys=[f for f in store.find(kind="Key", subject=right_rel) if tuple(dict(f.payload).get("columns",()))==(right_col,)]
    if not keys: return _unknown(rule, cert, "no uniqueness fact for right join relation")
    return _accept(rule, cert, [Fact.make("Fanout", node.name, {"direction":"left_to_output","max":1}, [keys[0].id])])

def group_grain(node, cert, store):
    rule="group_grain"
    if node.op != "Group": return _reject(rule, cert, "operator is not Group")
    expected=tuple(cert.witness.get("grain",())); actual=tuple(node.args.get("group_by",()))
    if actual!=expected: return _reject(rule, cert, f"grouping keys {actual} differ from witness {expected}")
    return _accept(rule, cert, [Fact.make("Grain", node.name, {"columns":expected}, cert.assumptions)])

def restricted_flow(node, cert, store):
    rule="restricted_flow"; lineage=node.args.get("lineage")
    if lineage is None: return _unknown(rule, cert, "lineage metadata unavailable")
    restricted=set(cert.witness.get("restricted_sources",())); forbidden=set(cert.witness.get("forbidden_outputs",()))
    for out in forbidden:
        if restricted.intersection(set(lineage.get(out,()))): return _reject(rule, cert, f"restricted source reaches output {out}")
    return _accept(rule, cert, [Fact.make("RestrictedFlowSafe", node.name, {"forbidden_outputs":tuple(sorted(forbidden))}, cert.assumptions)])

def schema_compatible(node, cert, store):
    rule="schema_compatible"; actual=node.args.get("schema"); expected=cert.witness.get("expected"); mode=cert.witness.get("mode","exact")
    if actual is None or expected is None: return _unknown(rule, cert, "schema metadata unavailable")
    actual={str(k):str(v) for k,v in actual.items()}; expected={str(k):str(v) for k,v in expected.items()}
    if mode=="exact": ok=actual==expected
    elif mode=="contains": ok=all(actual.get(k)==v for k,v in expected.items())
    else: return _reject(rule, cert, f"unknown schema mode: {mode}")
    if not ok: return _reject(rule, cert, "schema obligation failed")
    return _accept(rule, cert, [Fact.make("Schema", node.name, {"columns":tuple(sorted(actual.items()))}, cert.assumptions)])

def filter_preserves_key(node, cert, store):
    rule="filter_preserves_key"
    if node.op != "Filter": return _reject(rule, cert, "operator is not Filter")
    source=cert.witness.get("source_relation"); cols=tuple(cert.witness.get("key_columns",()))
    keys=[f for f in store.find(kind="Key", subject=source) if tuple(dict(f.payload).get("columns",()))==cols]
    if not keys: return _unknown(rule, cert, "source key fact unavailable")
    return _accept(rule, cert, [Fact.make("Key", node.name, {"columns":cols}, [keys[0].id])])

def union_schema(node, cert, store):
    rule="union_schema"
    if node.op != "Union": return _reject(rule, cert, "operator is not Union")
    schemas=cert.witness.get("input_schemas",())
    if len(schemas)<2: return _unknown(rule, cert, "insufficient input schema evidence")
    canon=[tuple(sorted((str(k),str(v)) for k,v in s.items())) for s in schemas]
    if len(set(canon))!=1: return _reject(rule, cert, "union inputs have incompatible schemas")
    return _accept(rule, cert, [Fact.make("Schema", node.name, {"columns":canon[0]}, cert.assumptions)])

def default_registry():
    registry=RuleRegistry()
    for name,fn in {"project_key":project_key,"join_fanout":join_fanout,"group_grain":group_grain,"restricted_flow":restricted_flow,"schema_compatible":schema_compatible,"filter_preserves_key":filter_preserves_key,"union_schema":union_schema}.items(): registry.register(name,fn)
    return registry
