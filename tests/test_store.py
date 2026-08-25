import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from certiflow import Fact,FactStore

def test_dependency_invalidation():
    store=FactStore();root=Fact.make("Key","customers",{"columns":("id",)});root_id=store.add(root);derived=Fact.make("Fanout","joined",{"max":1},[root_id]);derived_id=store.add(derived);downstream=Fact.make("Grain","agg",{"columns":("region",)},[derived_id]);downstream_id=store.add(downstream);doomed=store.invalidate([root_id]);assert doomed=={root_id,derived_id,downstream_id};assert not store.by_id
