from __future__ import annotations
from typing import Mapping, Sequence
from ..model import IRNode


def scan(name: str, schema: Mapping[str, str], engine: str = "generic") -> IRNode:
    return IRNode("Scan", name, {"schema": dict(schema)}, engine=engine, source_ref=name)


def project(name: str, source: str, mapping: Mapping[str, str], engine: str = "generic") -> IRNode:
    return IRNode("Project", name, {"mapping": dict(mapping)}, inputs=(source,), engine=engine)


def filter_(name: str, source: str, predicate: str, engine: str = "generic") -> IRNode:
    return IRNode("Filter", name, {"predicate": predicate}, inputs=(source,), engine=engine)


def join(name: str, left: str, right: str, equi: Sequence[tuple[str, str]],
         join_type: str = "inner", engine: str = "generic") -> IRNode:
    return IRNode("Join", name, {"join_type": join_type, "equi": tuple(equi)},
                  inputs=(left, right), engine=engine)


def group(name: str, source: str, group_by: Sequence[str], aggregates: Mapping[str, str],
          engine: str = "generic") -> IRNode:
    return IRNode("Group", name, {"group_by": tuple(group_by), "aggregates": dict(aggregates)},
                  inputs=(source,), engine=engine)
