from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from ..dbt_sql import normalize_dbt_model
from ..sqlnorm import SQLNormalizationError

@dataclass
class CorpusResult:
    files: int
    normalized: int
    rejected: int
    nodes: int
    opaque_expressions: int
    opaque_relations: int
    failures: dict[str, str]
    def as_dict(self): return asdict(self)

def evaluate_dbt_directory(path: str | Path) -> CorpusResult:
    root=Path(path); files=sorted(root.rglob('*.sql')); ok=nodes=opaque=opaque_relations=0; failures={}
    for file in files:
        try:
            result=normalize_dbt_model(file.read_text(encoding='utf-8'), model_name=file.stem)
            ok+=1; nodes+=len(result.graph.nodes); opaque+=result.opaque_expressions; opaque_relations+=result.opaque_relations
        except SQLNormalizationError as exc:
            failures[str(file.relative_to(root))]=str(exc)
    return CorpusResult(len(files),ok,len(files)-ok,nodes,opaque,opaque_relations,failures)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('path'); a=p.parse_args(); print(json.dumps(evaluate_dbt_directory(a.path).as_dict(),indent=2,sort_keys=True))
