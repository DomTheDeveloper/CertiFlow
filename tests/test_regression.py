import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from certiflow import Certificate,Checker,Fact,IRNode,Verdict

def run_regression():
    checker=Checker();checker.store.add(Fact.make("Key","customers",{"columns":("customer_id",)}));join=IRNode("Join","orders_customers",{"join_type":"left","equi":(("customer_id","customer_id"),)},("orders","customers"));r1=checker.verify(join,Certificate(join.hash,"join_fanout",witness={"left_col":"customer_id","right_col":"customer_id","right_relation":"customers"}));assert r1.verdict==Verdict.ACCEPT;group=IRNode("Group","revenue_by_region",{"group_by":("region",),"aggregates":{"revenue":"sum(amount)"}},(join.name,));r2=checker.verify(group,Certificate(group.hash,"group_grain",assumptions=(r1.claims[0].id,),witness={"grain":("region",)}));assert r2.verdict==Verdict.ACCEPT;assert checker.verify(join,Certificate("0"*64,"join_fanout")).verdict==Verdict.REJECT;return 3

def test_regression():assert run_regression()==3
