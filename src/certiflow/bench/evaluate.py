from __future__ import annotations
from dataclasses import dataclass, asdict, replace
import json
from typing import Callable
from ..checker import Checker
from ..model import Certificate, Fact, IRNode, Verdict
from .faults import mutate_group_grain, mutate_join_key, mutate_projection, mutate_schema, mutate_restricted_flow

@dataclass
class FaultEvalResult:
    family: str; trials: int; rejected: int; unknown: int; accepted: int
    def as_dict(self) -> dict: return asdict(self)

def _evaluate(family: str, trials: int, make_case: Callable):
    counts = {Verdict.REJECT: 0, Verdict.UNKNOWN: 0, Verdict.ACCEPT: 0}
    for i in range(trials):
        checker, node, cert, mutator = make_case(i)
        mutated = mutator(node)
        rebound = replace(cert, subject_hash=mutated.hash)
        result = checker.verify(mutated, rebound)
        counts[result.verdict] += 1
    return FaultEvalResult(family, trials, counts[Verdict.REJECT], counts[Verdict.UNKNOWN], counts[Verdict.ACCEPT])

def run_fault_evaluation(trials: int = 100) -> list[FaultEvalResult]:
    def join_case(i):
        checker=Checker(); checker.store.add(Fact.make("Key","customers",{"columns":("customer_id",)})); node=IRNode("Join",f"join_{i}",{"join_type":"left","equi":(("customer_id","customer_id"),)},("orders","customers")); cert=Certificate(node.hash,"join_fanout",witness={"left_col":"customer_id","right_col":"customer_id","right_relation":"customers"}); return checker,node,cert,mutate_join_key
    def group_case(i):
        checker=Checker(); node=IRNode("Group",f"group_{i}",{"group_by":("region",),"aggregates":{"revenue":"sum(amount)"}},("orders",)); return checker,node,Certificate(node.hash,"group_grain",witness={"grain":("region",)}),mutate_group_grain
    def project_case(i):
        checker=Checker(); node=IRNode("Project",f"project_{i}",{"mapping":{"id":"customer_id","region":"region"}},("customers",)); return checker,node,Certificate(node.hash,"project_key",witness={"source_key":("customer_id",),"output_key":("id",)}),mutate_projection
    def schema_case(i):
        checker=Checker(); node=IRNode("Scan",f"schema_{i}",{"schema":{"id":"int","email":"text"}}); return checker,node,Certificate(node.hash,"schema_compatible",witness={"expected":{"id":"int","email":"text"},"mode":"exact"}),mutate_schema
    def flow_case(i):
        checker=Checker(); node=IRNode("Project",f"flow_{i}",{"lineage":{"public":["id"],"display":["name"]}}); return checker,node,Certificate(node.hash,"restricted_flow",witness={"restricted_sources":["ssn"],"forbidden_outputs":["public","display"]}),mutate_restricted_flow
    return [_evaluate("join-key",trials,join_case),_evaluate("aggregation-grain",trials,group_case),_evaluate("projection-key",trials,project_case),_evaluate("schema-drift",trials,schema_case),_evaluate("restricted-flow",trials,flow_case)]

def main(argv=None) -> int:
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("--trials",type=int,default=100); args=p.parse_args(argv)
    print(json.dumps([r.as_dict() for r in run_fault_evaluation(args.trials)],indent=2,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
