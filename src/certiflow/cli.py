from __future__ import annotations
import argparse,json
from .adapters.dbt import DbtManifestAdapter
from .bench.runner import run_incremental_benchmark
from .checker import Checker
from .graph import PipelineGraph
from .model import Fact,Verdict
from .serde import cert_from_dict,load_json,node_from_dict

def cmd_benchmark(a): print(json.dumps(run_incremental_benchmark(a.nodes,a.seed,a.position).as_dict(),indent=2,sort_keys=True)); return 0
def cmd_dbt_summary(a):
    ad=DbtManifestAdapter.from_path(a.manifest); nodes=list(ad.nodes()); g=PipelineGraph.from_nodes(nodes); print(json.dumps({"nodes":len(nodes),"topological_order_head":g.topological_order()[:10],"seed_facts":[f.as_dict() for f in ad.seed_facts()]},indent=2,sort_keys=True)); return 0
def cmd_verify(a):
    payload=load_json(a.input); node=node_from_dict(payload["node"]); checker=Checker()
    for f in payload.get("facts",()): checker.store.add(Fact.make(f["kind"],f["subject"],f.get("payload",{}),f.get("deps",()),f.get("strength","invariant")))
    r=checker.verify(node,cert_from_dict(payload["certificate"])); print(json.dumps({"verdict":r.verdict.value,"reason":r.reason,"claims":[f.as_dict() for f in r.claims],"certificate_id":r.certificate_id},indent=2,sort_keys=True)); return 0 if r.verdict==Verdict.ACCEPT else 2
def build_parser():
    p=argparse.ArgumentParser(prog="certiflow"); sub=p.add_subparsers(dest="command",required=True); b=sub.add_parser("benchmark"); b.add_argument("--nodes",type=int,default=1000); b.add_argument("--seed",type=int,default=7); b.add_argument("--position",type=float,default=.5); b.set_defaults(func=cmd_benchmark); d=sub.add_parser("dbt-summary"); d.add_argument("manifest"); d.set_defaults(func=cmd_dbt_summary); v=sub.add_parser("verify"); v.add_argument("input"); v.set_defaults(func=cmd_verify); return p
def main(argv=None): a=build_parser().parse_args(argv); return a.func(a)
if __name__=="__main__": raise SystemExit(main())
