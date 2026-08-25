import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from certiflow import Fact,FactStore

def test_dependency_invalidation():
    s=FactStore(); r=Fact.make("Key","customers",{"columns":("id",)}); rid=s.add(r); d=Fact.make("Fanout","joined",{"max":1},[rid]); did=s.add(d); x=Fact.make("Grain","agg",{"columns":("region",)},[did]); xid=s.add(x); assert s.invalidate([rid])=={rid,did,xid}; assert not s.by_id
