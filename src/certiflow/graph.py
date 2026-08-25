from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, Iterable, List, Set
from .model import IRNode


class GraphError(ValueError):
    pass


@dataclass
class PipelineGraph:
    nodes: Dict[str, IRNode]

    @classmethod
    def from_nodes(cls, nodes: Iterable[IRNode]) -> "PipelineGraph":
        mapping = {}
        for node in nodes:
            if node.name in mapping:
                raise GraphError(f"duplicate node name: {node.name}")
            mapping[node.name] = node
        graph = cls(mapping)
        graph.topological_order()
        return graph

    def children(self) -> dict[str, set[str]]:
        out: dict[str, set[str]] = defaultdict(set)
        for node in self.nodes.values():
            for parent in node.inputs:
                if parent in self.nodes:
                    out[parent].add(node.name)
        return out

    def topological_order(self) -> List[str]:
        indegree = {name: 0 for name in self.nodes}
        children = self.children()
        for node in self.nodes.values():
            indegree[node.name] += sum(1 for p in node.inputs if p in self.nodes)
        q = deque(sorted(n for n, d in indegree.items() if d == 0))
        order = []
        while q:
            n = q.popleft()
            order.append(n)
            for c in sorted(children.get(n, ())):
                indegree[c] -= 1
                if indegree[c] == 0:
                    q.append(c)
        if len(order) != len(self.nodes):
            raise GraphError("pipeline contains a cycle")
        return order

    def descendants(self, changed: Iterable[str]) -> Set[str]:
        children = self.children()
        seen: Set[str] = set()
        q = deque(changed)
        while q:
            n = q.popleft()
            if n in seen:
                continue
            seen.add(n)
            q.extend(children.get(n, ()))
        return seen

    def diff(self, other: "PipelineGraph") -> set[str]:
        names = set(self.nodes) | set(other.nodes)
        changed = set()
        for name in names:
            left, right = self.nodes.get(name), other.nodes.get(name)
            if left is None or right is None or left.hash != right.hash:
                changed.add(name)
        return changed
