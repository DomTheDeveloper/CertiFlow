from __future__ import annotations
from dataclasses import replace
import time,json,statistics
from ..adapters.sql import filter_,project,scan
from ..graph import PipelineGraph

def branched_pipeline(branches=20,depth=100):
    nodes=[scan("root",{"id":"int","value":"decimal"})]
    for b in range(branches):
        current="root"
        for d in range(depth):
            name=f"b{b:03d}_n{d:04d}"; node=filter_(name,current,f"value >= {d}") if d%2==0 else project(name,current,{"id":"id","value":"value"}); nodes.append(node); current=name
    return PipelineGraph.from_nodes(nodes)
def run_invalidation_benchmark(branches=20,depth=100,repeats=7):
    samples=[]
    for _ in range(repeats):
        g=branched_pipeline(branches,depth); target=f"b{branches//2:03d}_n{depth//2:04d}"; mapping=dict(g.nodes); node=mapping[target]; args=dict(node.args); args["edited"]=True; mapping[target]=replace(node,args=args); changed=PipelineGraph(mapping); t=time.perf_counter(); affected=g.descendants(g.diff(changed)); samples.append(((time.perf_counter()-t)*1000,len(affected)))
    total=1+branches*depth
    return {"nodes":total,"branches":branches,"depth":depth,"affected_nodes":int(statistics.median(x[1] for x in samples)),"affected_fraction":statistics.median(x[1] for x in samples)/total,"invalidation_ms_median":statistics.median(x[0] for x in samples),"repeats":repeats}
if __name__=="__main__":
    import argparse; p=argparse.ArgumentParser(); p.add_argument("--branches",type=int,default=20); p.add_argument("--depth",type=int,default=100); p.add_argument("--repeats",type=int,default=7); a=p.parse_args(); print(json.dumps(run_invalidation_benchmark(a.branches,a.depth,a.repeats),indent=2,sort_keys=True))
