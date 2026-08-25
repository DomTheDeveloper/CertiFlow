from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping
from ..model import Fact
from ..store import FactStore

@dataclass(frozen=True)
class Requirement:
    kind: str
    subject: str
    payload_contains: Mapping[str, Any] = field(default_factory=dict)

@dataclass
class GateResult:
    allowed: bool
    satisfied: list[Requirement]
    missing: list[Requirement]

class Gate:
    """A CI/deployment gate over accepted facts, not producer assertions."""
    def __init__(self, requirements: Iterable[Requirement]) -> None:
        self.requirements = tuple(requirements)

    @staticmethod
    def _matches(fact: Fact, req: Requirement) -> bool:
        if fact.kind != req.kind or fact.subject != req.subject:
            return False
        payload = dict(fact.payload)
        return all(payload.get(k) == v for k, v in req.payload_contains.items())

    def evaluate(self, store: FactStore) -> GateResult:
        satisfied, missing = [], []
        for req in self.requirements:
            if any(self._matches(f, req) for f in store.find(kind=req.kind, subject=req.subject)):
                satisfied.append(req)
            else:
                missing.append(req)
        return GateResult(not missing, satisfied, missing)
