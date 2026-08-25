from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


def canonical_hash(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return sha256(payload).hexdigest()


class Verdict(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Fact:
    kind: str
    subject: str
    payload: Tuple[Tuple[str, Any], ...]
    deps: Tuple[str, ...] = ()
    strength: str = "invariant"

    @staticmethod
    def make(kind: str, subject: str, payload: Mapping[str, Any], deps: Iterable[str] = (), strength: str = "invariant") -> "Fact":
        return Fact(kind, subject, tuple(sorted(payload.items())), tuple(sorted(deps)), strength)

    def as_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "subject": self.subject, "payload": dict(self.payload), "deps": list(self.deps), "strength": self.strength}

    @property
    def id(self) -> str:
        return canonical_hash(self.as_dict())


@dataclass(frozen=True)
class IRNode:
    op: str
    name: str
    args: Mapping[str, Any]
    inputs: Tuple[str, ...] = ()

    def canonical(self) -> Dict[str, Any]:
        return {"op": self.op, "name": self.name, "args": self.args, "inputs": list(self.inputs)}

    @property
    def hash(self) -> str:
        return canonical_hash(self.canonical())


@dataclass(frozen=True)
class Certificate:
    subject_hash: str
    rule: str
    assumptions: Tuple[str, ...]
    claims: Tuple[Fact, ...]
    witness: Mapping[str, Any]
    producer: str = "untrusted"


@dataclass
class CheckResult:
    verdict: Verdict
    claims: List[Fact] = field(default_factory=list)
    reason: str = ""


class FactStore:
    def __init__(self) -> None:
        self.by_id: Dict[str, Fact] = {}

    def add(self, fact: Fact) -> str:
        self.by_id[fact.id] = fact
        return fact.id

    def has(self, fact_id: str) -> bool:
        return fact_id in self.by_id

    def find(self, *, kind: str, subject: Optional[str] = None) -> List[Fact]:
        return [f for f in self.by_id.values() if f.kind == kind and (subject is None or f.subject == subject)]


class Checker:
    """Small deterministic checker. Certificate producers are never trusted."""

    def __init__(self, store: FactStore) -> None:
        self.store = store

    def verify(self, node: IRNode, cert: Certificate) -> CheckResult:
        if cert.subject_hash != node.hash:
            return CheckResult(Verdict.REJECT, reason="subject hash mismatch")
        missing = [fid for fid in cert.assumptions if not self.store.has(fid)]
        if missing:
            return CheckResult(Verdict.UNKNOWN, reason=f"missing assumptions: {missing}")
        fn = getattr(self, f"_rule_{cert.rule}", None)
        if fn is None:
            return CheckResult(Verdict.REJECT, reason=f"unknown rule {cert.rule}")
        result = fn(node, cert)
        if result.verdict == Verdict.ACCEPT:
            for fact in result.claims:
                self.store.add(fact)
        return result

    def _rule_project_key(self, node: IRNode, cert: Certificate) -> CheckResult:
        if node.op != "Project":
            return CheckResult(Verdict.REJECT, reason="wrong operator")
        mapping = node.args.get("mapping", {})
        src_key = cert.witness.get("source_key")
        out_key = cert.witness.get("output_key")
        if not src_key or not out_key or len(src_key) != len(out_key):
            return CheckResult(Verdict.REJECT, reason="malformed key witness")
        for s, o in zip(src_key, out_key):
            if mapping.get(o) != s:
                return CheckResult(Verdict.REJECT, reason=f"projection does not preserve {s}->{o}")
        claim = Fact.make("Key", node.name, {"columns": tuple(out_key)}, cert.assumptions)
        return CheckResult(Verdict.ACCEPT, [claim])

    def _rule_join_fanout(self, node: IRNode, cert: Certificate) -> CheckResult:
        if node.op != "Join" or node.args.get("join_type", "inner") not in {"inner", "left"}:
            return CheckResult(Verdict.REJECT, reason="unsupported join")
        left_col = cert.witness.get("left_col")
        right_col = cert.witness.get("right_col")
        if (left_col, right_col) not in tuple(node.args.get("equi", ())):
            return CheckResult(Verdict.REJECT, reason="join witness does not match normalized predicate")
        right_rel = cert.witness.get("right_relation")
        keys = [f for f in self.store.find(kind="Key", subject=right_rel) if tuple(dict(f.payload).get("columns", ())) == (right_col,)]
        if not keys:
            return CheckResult(Verdict.UNKNOWN, reason="no uniqueness fact for join side")
        claim = Fact.make("Fanout", node.name, {"direction": "left_to_output", "max": 1}, [keys[0].id])
        return CheckResult(Verdict.ACCEPT, [claim])

    def _rule_group_grain(self, node: IRNode, cert: Certificate) -> CheckResult:
        if node.op != "Group":
            return CheckResult(Verdict.REJECT, reason="wrong operator")
        expected = tuple(cert.witness.get("grain", ()))
        if tuple(node.args.get("group_by", ())) != expected:
            return CheckResult(Verdict.REJECT, reason="grouping keys differ from witness")
        claim = Fact.make("Grain", node.name, {"columns": expected}, cert.assumptions)
        return CheckResult(Verdict.ACCEPT, [claim])

    def _rule_restricted_flow(self, node: IRNode, cert: Certificate) -> CheckResult:
        lineage = node.args.get("lineage", {})
        restricted = set(cert.witness.get("restricted_sources", ()))
        forbidden_outputs = set(cert.witness.get("forbidden_outputs", ()))
        for out_col in forbidden_outputs:
            if restricted.intersection(set(lineage.get(out_col, ()))):
                return CheckResult(Verdict.REJECT, reason=f"restricted source reaches {out_col}")
        claim = Fact.make("RestrictedFlowSafe", node.name, {"forbidden_outputs": tuple(sorted(forbidden_outputs))}, cert.assumptions)
        return CheckResult(Verdict.ACCEPT, [claim])


def example_pipeline() -> Tuple[List[IRNode], FactStore, Checker]:
    store = FactStore()
    store.add(Fact.make("Key", "customers", {"columns": ("customer_id",)}))
    join = IRNode(op="Join", name="orders_customers", args={"join_type": "left", "equi": (("customer_id", "customer_id"),)}, inputs=("orders", "customers"))
    group = IRNode(op="Group", name="revenue_by_region", args={"group_by": ("region",), "aggregates": {"revenue": "sum(amount)"}}, inputs=(join.name,))
    return [join, group], store, Checker(store)
