from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from .model import Certificate, IRNode
from .store import FactStore


@dataclass
class InferenceProducer:
    """
    Untrusted convenience producer for the certifiable relational fragment.

    This class emits candidate certificates. The Checker remains the authority:
    producer output has no effect unless the independent rule implementation accepts it.
    """

    producer_id: str = "builtin-inference-v1"

    def candidates(self, node: IRNode, store: FactStore) -> Iterable[Certificate]:
        if node.op == "Project" and node.inputs:
            source = node.inputs[0]
            mapping = dict(node.args.get("mapping", {}))
            for key in store.find(kind="Key", subject=source):
                src = tuple(dict(key.payload).get("columns", ()))
                reverse = {src_col: out_col for out_col, src_col in mapping.items()}
                if all(c in reverse for c in src):
                    out = tuple(reverse[c] for c in src)
                    yield Certificate(
                        node.hash, "project_key", assumptions=(key.id,),
                        witness={"source_key": src, "output_key": out},
                        producer=self.producer_id,
                    )

        elif node.op == "Filter" and node.inputs:
            source = node.inputs[0]
            for key in store.find(kind="Key", subject=source):
                cols = tuple(dict(key.payload).get("columns", ()))
                yield Certificate(
                    node.hash, "filter_preserves_key", assumptions=(key.id,),
                    witness={"source_relation": source, "key_columns": cols},
                    producer=self.producer_id,
                )

        elif node.op == "Join" and len(node.inputs) == 2:
            right = node.inputs[1]
            for left_col, right_col in tuple(tuple(x) for x in node.args.get("equi", ())):
                yield Certificate(
                    node.hash, "join_fanout",
                    witness={"left_col": left_col, "right_col": right_col, "right_relation": right},
                    producer=self.producer_id,
                )

        elif node.op == "Group":
            yield Certificate(
                node.hash, "group_grain",
                witness={"grain": tuple(node.args.get("group_by", ()))},
                producer=self.producer_id,
            )

        if "schema" in node.args:
            yield Certificate(
                node.hash, "schema_compatible",
                witness={"expected": dict(node.args["schema"]), "mode": "exact"},
                producer=self.producer_id,
            )
