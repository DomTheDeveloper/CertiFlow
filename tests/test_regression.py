import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from certiflow import Certificate,Checker,Fact,IRNode,Verdict

def test_regression():
    c=Checker(); c.store.add(Fact.make("Key","customers",{"columns":("customer_id",)})); j=IRNode("Join","orders_customers",{"join_type":"left","equi":(("customer_id","customer_id"),)},("orders","customers")); r1=c.verify(j,Certificate(j.hash,"join_fanout",witness={"left_col":"customer_id","right_col":"customer_id","right_relation":"customers"})); assert r1.verdict==Verdict.ACCEPT; g=IRNode("Group","revenue_by_region",{"group_by":("region",),"aggregates":{"revenue":"sum(amount)"}},(j.name,)); assert c.verify(g,Certificate(g.hash,"group_grain",assumptions=(r1.claims[0].id,),witness={"grain":("region",)})).verdict==Verdict.ACCEPT; assert c.verify(j,Certificate("0"*64,"join_fanout")).verdict==Verdict.REJECT
