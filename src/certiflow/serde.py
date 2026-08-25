from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .model import Certificate, Fact, IRNode


def node_from_dict(d: dict[str, Any]) -> IRNode:
    return IRNode(
        op=d["op"], name=d["name"], args=d.get("args", {}),
        inputs=tuple(d.get("inputs", ())), engine=d.get("engine", "generic"),
        source_ref=d.get("source_ref", "")
    )


def fact_from_dict(d: dict[str, Any]) -> Fact:
    return Fact.make(
        d["kind"], d["subject"], d.get("payload", {}),
        d.get("deps", ()), d.get("strength", "invariant")
    )


def cert_from_dict(d: dict[str, Any]) -> Certificate:
    return Certificate(
        subject_hash=d["subject_hash"], rule=d["rule"],
        assumptions=tuple(d.get("assumptions", ())),
        claims=tuple(fact_from_dict(x) for x in d.get("claims", ())),
        witness=d.get("witness", {}), producer=d.get("producer", "untrusted"),
        version=int(d.get("version", 1)),
    )


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(value: Any, path: str | Path) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(value, fh, indent=2, sort_keys=True)
        fh.write("\n")
