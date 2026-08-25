from __future__ import annotations
from dataclasses import dataclass,asdict
import json,time
from .workload import synthetic_pipeline
from ..graph import PipelineGraph

@dataclass
class BenchResult:
    nodes:int;graph_build_ms:float;topo_ms:float;diff_ms:float;affected_nodes:int
    def as_dict(self)->dict:return asdict(self)

def run_incremental_benchmark(nodes:int=1000,seed:int=7,position:float=0.5)->BenchResult:
    t0=time.perf_counter();graph,_=synthetic_pipeline(nodes,seed);t1=time.perf_counter();graph.topological_order();t2=time.perf_counter()
    mapping=dict(graph.nodes);ordered=graph.topological_order();target_index=min(len(ordered)-1,max(0,int((len(ordered)-1)*position)))
    candidates=[graph.nodes[n] for n in ordered[target_index:] if graph.nodes[n].op=="Filter"]
    if not candidates:candidates=[graph.nodes[n] for n in reversed(ordered[:target_index+1]) if graph.nodes[n].op=="Filter"]
    candidate=candidates[0] if candidates else graph.nodes[ordered[target_index]];args=dict(candidate.args);args["benchmark_mutation"]=True
    from dataclasses import replace
    mapping[candidate.name]=replace(candidate,args=args);changed=PipelineGraph(mapping);t3=time.perf_counter();changed_names=graph.diff(changed);affected=graph.descendants(changed_names);t4=time.perf_counter()
    return BenchResult(nodes,(t1-t0)*1000,(t2-t1)*1000,(t4-t3)*1000,len(affected))
def main(argv=None)->int:
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--nodes",type=int,default=1000);p.add_argument("--seed",type=int,default=7);p.add_argument("--position",type=float,default=0.5);a=p.parse_args(argv);print(json.dumps(run_incremental_benchmark(a.nodes,a.seed,a.position).as_dict(),indent=2,sort_keys=True));return 0
