import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from certiflow import Certificate,Checker,IRNode
from certiflow.policy import AuditLedger,Gate,Requirement

def test_policy_gate_only_accepts_checked_facts():
    c=Checker();p=IRNode("Project","public_customers",{"mapping":{"id":"customer_id"}},("customers",));r=c.verify(p,Certificate(p.hash,"project_key",witness={"source_key":("customer_id",),"output_key":("id",)}));assert r.accepted;assert Gate([Requirement("Key","public_customers",{"columns":("id",)})]).evaluate(c.store).allowed;assert not Gate([Requirement("Grain","public_customers",{})]).evaluate(c.store).allowed

def test_hash_chained_audit_ledger():
    c=Checker();n=IRNode("Group","g",{"group_by":("region",)},("x",));r=c.verify(n,Certificate(n.hash,"group_grain",witness={"grain":("region",)}));ledger=AuditLedger();e1=ledger.append(n,r,timestamp="2026-08-25T00:00:00+00:00");e2=ledger.append(n,r,timestamp="2026-08-25T00:00:01+00:00");assert e2.previous_hash==e1.hash;assert ledger.verify_chain()
