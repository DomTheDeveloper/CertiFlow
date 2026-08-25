from __future__ import annotations
from .model import Certificate, CheckResult, IRNode, Verdict
from .rules import RuleRegistry, default_registry
from .store import FactStore


class Checker:
    """Small deterministic verifier. Certificate producers are not trusted."""

    def __init__(self, store: FactStore | None = None, registry: RuleRegistry | None = None) -> None:
        self.store = store or FactStore()
        self.registry = registry or default_registry()

    def verify(self, node: IRNode, cert: Certificate) -> CheckResult:
        if cert.subject_hash != node.hash:
            return CheckResult(Verdict.REJECT, reason="subject hash mismatch; certificate is stale or bound to another node", rule=cert.rule, certificate_id=cert.id)
        missing = [fid for fid in cert.assumptions if not self.store.has(fid)]
        if missing:
            return CheckResult(Verdict.UNKNOWN, reason=f"missing assumptions: {missing}", rule=cert.rule, certificate_id=cert.id)
        rule = self.registry.get(cert.rule)
        if rule is None:
            return CheckResult(Verdict.REJECT, reason=f"unknown rule: {cert.rule}", rule=cert.rule, certificate_id=cert.id)
        result = rule(node, cert, self.store)
        if result.verdict == Verdict.ACCEPT:
            self.store.add_many(result.claims)
        return result
