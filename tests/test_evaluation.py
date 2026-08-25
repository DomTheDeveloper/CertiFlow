import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from certiflow.bench.evaluate import run_fault_evaluation

def test_semantic_fault_evaluation_rejects_mutants():
    rows=run_fault_evaluation(10); assert len(rows)==3; assert sum(r.accepted for r in rows)==0; assert sum(r.rejected+r.unknown for r in rows)==30
