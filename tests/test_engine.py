import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from certiflow.bench.workload import synthetic_pipeline
from certiflow.engine import VerificationEngine

def test_end_to_end_inference_engine():
    graph,facts=synthetic_pipeline(30,3); r=VerificationEngine().verify(graph,facts); assert r.nodes==30; assert r.certificates>0; assert r.accepted>0; assert r.rejected==0; assert 0.0<r.acceptance_rate<=1.0
