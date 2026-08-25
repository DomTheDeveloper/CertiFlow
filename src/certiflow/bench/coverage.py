from __future__ import annotations
import json
from ..engine import VerificationEngine
from .workload import synthetic_pipeline

def run_coverage(nodes=1000,seed=7):
    graph,facts=synthetic_pipeline(nodes,seed); return VerificationEngine().verify(graph,facts).summary()
if __name__=="__main__":
    import argparse; p=argparse.ArgumentParser(); p.add_argument("--nodes",type=int,default=1000); p.add_argument("--seed",type=int,default=7); a=p.parse_args(); print(json.dumps(run_coverage(a.nodes,a.seed),indent=2,sort_keys=True))
