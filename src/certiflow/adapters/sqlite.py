from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from .base import Adapter
from ..model import Fact, IRNode


class SQLiteAdapter(Adapter):
    """Live SQLite catalog adapter using only the Python standard library.

    The adapter extracts table schemas, primary keys, and single/multi-column
    unique indexes. It never executes user queries; metadata is obtained from
    SQLite PRAGMA statements.
    """

    def __init__(self, connection: sqlite3.Connection, *, source: str = "sqlite") -> None:
        self.connection = connection
        self.source = source

    @classmethod
    def from_path(cls, path: str | Path) -> "SQLiteAdapter":
        path = str(path)
        return cls(sqlite3.connect(path), source=path)

    def table_names(self) -> list[str]:
        rows = self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return [str(r[0]) for r in rows]

    @staticmethod
    def _quote_ident(name: str) -> str:
        return '"' + name.replace('"', '""') + '"'

    def _table_info(self, table: str):
        return self.connection.execute(f"PRAGMA table_info({self._quote_ident(table)})").fetchall()

    def nodes(self) -> Iterable[IRNode]:
        for table in self.table_names():
            rows = self._table_info(table)
            schema = {str(r[1]): str(r[2] or "unknown").lower() for r in rows}
            nullable = {str(r[1]): not bool(r[3]) for r in rows}
            yield IRNode(
                "Scan",
                table,
                {"schema": schema, "nullable": nullable},
                engine="sqlite",
                source_ref=f"{self.source}:{table}",
            )

    def seed_facts(self) -> Iterable[Fact]:
        for table in self.table_names():
            info = self._table_info(table)
            # SQLite primary-key ordinals are 1..N for composite PKs.
            pk = tuple(str(r[1]) for r in sorted(info, key=lambda r: int(r[5] or 0)) if int(r[5] or 0) > 0)
            if pk:
                yield Fact.make("Key", table, {"columns": pk, "source": "sqlite-primary-key"})

            for idx in self.connection.execute(f"PRAGMA index_list({self._quote_ident(table)})").fetchall():
                # seq, name, unique, origin, partial
                if not bool(idx[2]) or bool(idx[4]):
                    continue
                index_name = str(idx[1])
                cols = tuple(
                    str(r[2])
                    for r in sorted(
                        self.connection.execute(f"PRAGMA index_info({self._quote_ident(index_name)})").fetchall(),
                        key=lambda r: int(r[0]),
                    )
                    if r[2] is not None
                )
                if cols and cols != pk:
                    yield Fact.make("Key", table, {"columns": cols, "source": "sqlite-unique-index", "index": index_name})

    def close(self) -> None:
        self.connection.close()
