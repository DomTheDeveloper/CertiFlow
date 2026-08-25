from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable
from .base import Adapter
from ..model import Fact, IRNode


class DbtManifestAdapter(Adapter):
    """Dependency-free adapter for the stable subset of dbt manifest.json metadata."""

    def __init__(self, manifest: dict) -> None:
        self.manifest = manifest

    @classmethod
    def from_path(cls, path: str | Path) -> "DbtManifestAdapter":
        with open(path, "r", encoding="utf-8") as fh:
            return cls(json.load(fh))

    def nodes(self) -> Iterable[IRNode]:
        for unique_id, model in sorted(self.manifest.get("nodes", {}).items()):
            if model.get("resource_type") not in {"model", "seed", "snapshot"}:
                continue
            depends = tuple(
                dep for dep in model.get("depends_on", {}).get("nodes", ())
                if dep in self.manifest.get("nodes", {})
            )
            columns = model.get("columns", {})
            schema = {
                name: str(meta.get("data_type") or "unknown")
                for name, meta in columns.items()
            }
            yield IRNode(
                op="Opaque",
                name=unique_id,
                args={"schema": schema, "original_file_path": model.get("original_file_path", "")},
                inputs=depends,
                engine="dbt",
                source_ref=model.get("original_file_path", ""),
            )

    def seed_facts(self) -> Iterable[Fact]:
        for unique_id, model in sorted(self.manifest.get("nodes", {}).items()):
            for test in model.get("tests", ()):
                if isinstance(test, dict) and test.get("name") == "unique":
                    column = test.get("column_name")
                    if column:
                        yield Fact.make("Key", unique_id, {"columns": (column,)})
