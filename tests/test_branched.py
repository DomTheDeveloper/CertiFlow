import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from certiflow.bench.branched import branched_pipeline,run_invalidation_benchmark

def test_branched_pipeline_selective_invalidation():
    g=branched_pipeline(4,10); assert len(g.nodes)==41; r=run_invalidation_benchmark(4,10,2); assert 0<r["affected_fraction"]<0.5
