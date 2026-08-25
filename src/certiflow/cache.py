from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Iterable
from .model import Certificate, IRNode
from .graph import PipelineGraph


@dataclass
class CertificateCache:
    by_node_hash: Dict[str, list[Certificate]] = field(default_factory=dict)

    def put(self, node: IRNode, cert: Certificate) -> None:
        if cert.subject_hash != node.hash:
            raise ValueError("cannot cache certificate against a different node hash")
        self.by_node_hash.setdefault(node.hash, []).append(cert)

    def get(self, node: IRNode) -> tuple[Certificate, ...]:
        return tuple(self.by_node_hash.get(node.hash, ()))

    def invalidate_graph_change(self, old: PipelineGraph, new: PipelineGraph) -> set[str]:
        changed = old.diff(new)
        affected = old.descendants(changed) | new.descendants(changed)
        invalid_hashes = {
            graph.nodes[name].hash
            for graph in (old, new)
            for name in affected
            if name in graph.nodes
        }
        for h in invalid_hashes:
            self.by_node_hash.pop(h, None)
        return affected
