import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from certiflow.bench.workload import synthetic_pipeline
from certiflow.engine import VerificationEngine

def test_end_to_end_inference_engine():
    graph,facts=synthetic_pipeline(30,3);report=VerificationEngine().verify(graph,facts);assert report.nodes==30;assert report.certificates>0;assert report.accepted>0;assert report.rejected==0;assert 0.0<report.acceptance_rate<=1.0
