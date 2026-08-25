from __future__ import annotations
from collections import defaultdict, deque
from typing import Dict, Iterable, List, Optional, Set
from .model import Fact


class FactStore:
    """Content-addressed fact store with reverse dependency tracking."""

    def __init__(self) -> None:
        self.by_id: Dict[str, Fact] = {}
        self.reverse_deps: dict[str, set[str]] = defaultdict(set)
        self.by_subject: dict[str, set[str]] = defaultdict(set)

    def add(self, fact: Fact) -> str:
        fid = fact.id
        self.by_id[fid] = fact
        self.by_subject[fact.subject].add(fid)
        for dep in fact.deps:
            self.reverse_deps[dep].add(fid)
        return fid

    def add_many(self, facts: Iterable[Fact]) -> list[str]:
        return [self.add(f) for f in facts]

    def has(self, fact_id: str) -> bool:
        return fact_id in self.by_id

    def get(self, fact_id: str) -> Optional[Fact]:
        return self.by_id.get(fact_id)

    def find(self, *, kind: Optional[str] = None, subject: Optional[str] = None) -> List[Fact]:
        ids = self.by_subject.get(subject, set()) if subject is not None else self.by_id.keys()
        out = []
        for fid in ids:
            fact = self.by_id[fid]
            if kind is None or fact.kind == kind:
                out.append(fact)
        return sorted(out, key=lambda f: f.id)

    def invalidate(self, roots: Iterable[str]) -> set[str]:
        doomed: Set[str] = set()
        q = deque(roots)
        while q:
            fid = q.popleft()
            if fid in doomed:
                continue
            doomed.add(fid)
            q.extend(self.reverse_deps.get(fid, ()))
        for fid in doomed:
            fact = self.by_id.pop(fid, None)
            if fact:
                self.by_subject[fact.subject].discard(fid)
            self.reverse_deps.pop(fid, None)
        for deps in self.reverse_deps.values():
            deps.difference_update(doomed)
        return doomed

    def invalidate_subject(self, subject: str) -> set[str]:
        return self.invalidate(tuple(self.by_subject.get(subject, set())))

    def snapshot(self) -> dict:
        return {fid: fact.as_dict() for fid, fact in sorted(self.by_id.items())}
