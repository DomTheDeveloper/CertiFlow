import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from certiflow import Certificate, Checker, Fact, IRNode, Verdict

def test_join_fanout_accept_unknown_and_stale():
    checker=Checker(); checker.store.add(Fact.make("Key","customers",{"columns":("customer_id",)}))
    node=IRNode("Join","j",{"join_type":"left","equi":(("customer_id","customer_id"),)},("orders","customers"))
    cert=Certificate(node.hash,"join_fanout",witness={"left_col":"customer_id","right_col":"customer_id","right_relation":"customers"})
    assert checker.verify(node,cert).verdict==Verdict.ACCEPT
    wrong=IRNode("Join","j2",{"join_type":"left","equi":(("customer_id","region"),)},("orders","customers"))
    cert2=Certificate(wrong.hash,"join_fanout",witness={"left_col":"customer_id","right_col":"region","right_relation":"customers"})
    assert checker.verify(wrong,cert2).verdict==Verdict.UNKNOWN
    assert checker.verify(node,Certificate("0"*64,"join_fanout")).verdict==Verdict.REJECT

def test_project_group_schema_and_restricted_flow():
    c=Checker(); p=IRNode("Project","p",{"mapping":{"id":"customer_id","region":"region"}},("customers",)); r=c.verify(p,Certificate(p.hash,"project_key",witness={"source_key":("customer_id",),"output_key":("id",)})); assert r.verdict==Verdict.ACCEPT
    g=IRNode("Group","g",{"group_by":("region",),"aggregates":{"n":"count(*)"}},("p",)); assert c.verify(g,Certificate(g.hash,"group_grain",witness={"grain":("region",)})).verdict==Verdict.ACCEPT
    s=IRNode("Scan","s",{"schema":{"id":"int","email":"text"}}); assert c.verify(s,Certificate(s.hash,"schema_compatible",witness={"expected":{"id":"int"},"mode":"contains"})).verdict==Verdict.ACCEPT
    f=IRNode("Project","safe",{"lineage":{"public_id":["id"],"display":["name"]}}); assert c.verify(f,Certificate(f.hash,"restricted_flow",witness={"restricted_sources":["ssn"],"forbidden_outputs":["public_id","display"]})).verdict==Verdict.ACCEPT
