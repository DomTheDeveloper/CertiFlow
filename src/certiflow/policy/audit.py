from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable
from ..hashing import canonical_hash
from ..model import CheckResult, IRNode

@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    timestamp: str
    node: str
    node_hash: str
    verdict: str
    rule: str
    certificate_id: str
    reason: str
    previous_hash: str

    @property
    def hash(self) -> str:
        return canonical_hash(asdict(self))

class AuditLedger:
    """Hash-chained JSONL audit log for verification decisions."""
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(self, node: IRNode, result: CheckResult, *, timestamp: str | None = None) -> AuditEvent:
        previous = self.events[-1].hash if self.events else "0" * 64
        event = AuditEvent(
            sequence=len(self.events),
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            node=node.name,
            node_hash=node.hash,
            verdict=result.verdict.value,
            rule=result.rule,
            certificate_id=result.certificate_id,
            reason=result.reason,
            previous_hash=previous,
        )
        self.events.append(event)
        return event

    def verify_chain(self) -> bool:
        previous = "0" * 64
        for i, event in enumerate(self.events):
            if event.sequence != i or event.previous_hash != previous:
                return False
            previous = event.hash
        return True

    def write_jsonl(self, path: str | Path) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            for event in self.events:
                row = asdict(event); row["event_hash"] = event.hash
                fh.write(json.dumps(row, sort_keys=True) + "\n")
