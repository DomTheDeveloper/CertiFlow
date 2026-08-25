from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, Mapping, Tuple
from .hashing import canonical_hash


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
        return Fact(kind, subject, tuple(sorted(payload.items())), tuple(sorted(set(deps))), strength)

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
    engine: str = "generic"
    source_ref: str = ""

    def canonical(self) -> Dict[str, Any]:
        return {"op": self.op, "name": self.name, "args": self.args, "inputs": list(self.inputs), "engine": self.engine, "source_ref": self.source_ref}

    @property
    def hash(self) -> str:
        return canonical_hash(self.canonical())


@dataclass(frozen=True)
class Certificate:
    subject_hash: str
    rule: str
    assumptions: Tuple[str, ...] = ()
    claims: Tuple[Fact, ...] = ()
    witness: Mapping[str, Any] = field(default_factory=dict)
    producer: str = "untrusted"
    version: int = 1

    @property
    def id(self) -> str:
        return canonical_hash({"subject_hash": self.subject_hash, "rule": self.rule, "assumptions": self.assumptions, "claims": [c.as_dict() for c in self.claims], "witness": self.witness, "producer": self.producer, "version": self.version})


@dataclass
class CheckResult:
    verdict: Verdict
    claims: list[Fact] = field(default_factory=list)
    reason: str = ""
    rule: str = ""
    certificate_id: str = ""

    @property
    def accepted(self) -> bool:
        return self.verdict == Verdict.ACCEPT
