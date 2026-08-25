from __future__ import annotations
import json,statistics
from .runner import run_incremental_benchmark

def run_suite(repeats=7,sizes=(100,1000,5000),position=0.5):
    rows=[]
    for n in sizes:
        samples=[run_incremental_benchmark(n,7+i,position) for i in range(repeats)]
        rows.append({"nodes":n,"repeats":repeats,"affected_nodes_median":int(statistics.median(s.affected_nodes for s in samples)),"graph_build_ms_median":statistics.median(s.graph_build_ms for s in samples),"topo_ms_median":statistics.median(s.topo_ms for s in samples),"diff_ms_median":statistics.median(s.diff_ms for s in samples)})
    return rows
if __name__=="__main__":
    import argparse; p=argparse.ArgumentParser(); p.add_argument("--repeats",type=int,default=7); a=p.parse_args(); print(json.dumps(run_suite(a.repeats),indent=2,sort_keys=True))
