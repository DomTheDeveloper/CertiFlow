from __future__ import annotations
from dataclasses import dataclass,asdict,replace
import json
from ..checker import Checker
from ..model import Certificate,Fact,IRNode,Verdict
from .faults import mutate_group_grain,mutate_join_key,mutate_projection,mutate_schema,mutate_restricted_flow
@dataclass
class FaultEvalResult:
    family:str; trials:int; rejected:int; unknown:int; accepted:int
    def as_dict(self): return asdict(self)
def _evaluate(family,trials,make_case):
    counts={Verdict.REJECT:0,Verdict.UNKNOWN:0,Verdict.ACCEPT:0}
    for i in range(trials):
        checker,node,cert,mutator=make_case(i); mutated=mutator(node); result=checker.verify(mutated,replace(cert,subject_hash=mutated.hash)); counts[result.verdict]+=1
    return FaultEvalResult(family,trials,counts[Verdict.REJECT],counts[Verdict.UNKNOWN],counts[Verdict.ACCEPT])
def run_fault_evaluation(trials=100):
    def jc(i):
        c=Checker(); c.store.add(Fact.make("Key","customers",{"columns":("customer_id",)})); n=IRNode("Join",f"join_{i}",{"join_type":"left","equi":(("customer_id","customer_id"),)},("orders","customers")); return c,n,Certificate(n.hash,"join_fanout",witness={"left_col":"customer_id","right_col":"customer_id","right_relation":"customers"}),mutate_join_key
    def gc(i):
        c=Checker(); n=IRNode("Group",f"group_{i}",{"group_by":("region",),"aggregates":{"revenue":"sum(amount)"}},("orders",)); return c,n,Certificate(n.hash,"group_grain",witness={"grain":("region",)}),mutate_group_grain
    def pc(i):
        c=Checker(); n=IRNode("Project",f"project_{i}",{"mapping":{"id":"customer_id","region":"region"}},("customers",)); return c,n,Certificate(n.hash,"project_key",witness={"source_key":("customer_id",),"output_key":("id",)}),mutate_projection
    def sc(i):
        c=Checker(); n=IRNode("Scan",f"schema_{i}",{"schema":{"id":"int","email":"text"}}); return c,n,Certificate(n.hash,"schema_compatible",witness={"expected":{"id":"int","email":"text"},"mode":"exact"}),mutate_schema
    def fc(i):
        c=Checker(); n=IRNode("Project",f"flow_{i}",{"lineage":{"public":["id"],"display":["name"]}}); return c,n,Certificate(n.hash,"restricted_flow",witness={"restricted_sources":["ssn"],"forbidden_outputs":["public","display"]}),mutate_restricted_flow
    return [_evaluate("join-key",trials,jc),_evaluate("aggregation-grain",trials,gc),_evaluate("projection-key",trials,pc),_evaluate("schema-drift",trials,sc),_evaluate("restricted-flow",trials,fc)]
if __name__=="__main__":
    import argparse; p=argparse.ArgumentParser(); p.add_argument("--trials",type=int,default=100); a=p.parse_args(); print(json.dumps([r.as_dict() for r in run_fault_evaluation(a.trials)],indent=2,sort_keys=True))
