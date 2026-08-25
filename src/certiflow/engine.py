from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable
from .checker import Checker
from .graph import PipelineGraph
from .model import CheckResult, Fact, Verdict
from .producers import InferenceProducer


@dataclass
class VerificationReport:
    nodes: int = 0
    certificates: int = 0
    accepted: int = 0
    rejected: int = 0
    unknown: int = 0
    results: list[tuple[str, CheckResult]] = field(default_factory=list)

    @property
    def acceptance_rate(self) -> float:
        return 0.0 if self.certificates == 0 else self.accepted / self.certificates

    def summary(self) -> dict:
        return {"nodes": self.nodes, "certificates": self.certificates, "accepted": self.accepted, "rejected": self.rejected, "unknown": self.unknown, "acceptance_rate": self.acceptance_rate}


class VerificationEngine:
    def __init__(self, checker: Checker | None = None, producer: InferenceProducer | None = None) -> None:
        self.checker = checker or Checker()
        self.producer = producer or InferenceProducer()

    def verify(self, graph: PipelineGraph, seed_facts: Iterable[Fact] = ()) -> VerificationReport:
        self.checker.store.add_many(seed_facts)
        report = VerificationReport(nodes=len(graph.nodes))
        for name in graph.topological_order():
            node = graph.nodes[name]
            for cert in self.producer.candidates(node, self.checker.store):
                result = self.checker.verify(node, cert)
                report.certificates += 1
                report.results.append((name, result))
                if result.verdict == Verdict.ACCEPT:
                    report.accepted += 1
                elif result.verdict == Verdict.REJECT:
                    report.rejected += 1
                else:
                    report.unknown += 1
        return report
