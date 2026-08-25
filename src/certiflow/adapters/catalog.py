from __future__ import annotations
from typing import Iterable, Mapping, Sequence
from .base import Adapter
from ..model import Fact, IRNode


class CatalogAdapter(Adapter):
    """
    Engine-neutral adapter over introspection rows.
    Rows use: relation, column, type, nullable, ordinal, primary_key.
    """

    def __init__(self, rows: Sequence[Mapping[str, object]], engine: str = "catalog") -> None:
        self.rows = list(rows)
        self.engine = engine

    def _grouped(self) -> dict[str, list[Mapping[str, object]]]:
        grouped: dict[str, list[Mapping[str, object]]] = {}
        for row in self.rows:
            grouped.setdefault(str(row["relation"]), []).append(row)
        return grouped

    def nodes(self) -> Iterable[IRNode]:
        for relation, rows in sorted(self._grouped().items()):
            rows = sorted(rows, key=lambda r: int(r.get("ordinal", 0)))
            schema = {str(r["column"]): str(r.get("type", "unknown")) for r in rows}
            nullable = {str(r["column"]): bool(r.get("nullable", True)) for r in rows}
            yield IRNode(
                op="Scan", name=relation,
                args={"schema": schema, "nullable": nullable},
                engine=self.engine,
                source_ref=relation,
            )

    def seed_facts(self) -> Iterable[Fact]:
        for relation, rows in sorted(self._grouped().items()):
            pk = tuple(
                str(r["column"]) for r in sorted(rows, key=lambda r: int(r.get("ordinal", 0)))
                if bool(r.get("primary_key", False))
            )
            if pk:
                yield Fact.make("Key", relation, {"columns": pk})
