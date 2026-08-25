from __future__ import annotations
from dataclasses import dataclass, asdict, replace
import json,time
from .workload import synthetic_pipeline
from ..graph import PipelineGraph

@dataclass
class BenchResult:
    nodes:int; graph_build_ms:float; topo_ms:float; diff_ms:float; affected_nodes:int
    def as_dict(self): return asdict(self)

def run_incremental_benchmark(nodes=1000,seed=7,position=0.5):
    t0=time.perf_counter(); graph,_=synthetic_pipeline(nodes,seed); t1=time.perf_counter(); graph.topological_order(); t2=time.perf_counter()
    mapping=dict(graph.nodes); ordered=graph.topological_order(); idx=min(len(ordered)-1,max(0,int((len(ordered)-1)*position)))
    candidates=[graph.nodes[n] for n in ordered[idx:] if graph.nodes[n].op=="Filter"] or [graph.nodes[n] for n in reversed(ordered[:idx+1]) if graph.nodes[n].op=="Filter"]
    candidate=candidates[0] if candidates else graph.nodes[ordered[idx]]; args=dict(candidate.args); args["benchmark_mutation"]=True; mapping[candidate.name]=replace(candidate,args=args); changed=PipelineGraph(mapping); t3=time.perf_counter(); changed_names=graph.diff(changed); affected=graph.descendants(changed_names); t4=time.perf_counter()
    return BenchResult(nodes,(t1-t0)*1000,(t2-t1)*1000,(t4-t3)*1000,len(affected))
