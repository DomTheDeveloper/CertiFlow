import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from certiflow.bench.faults import mutate_group_grain,mutate_join_key,mutate_projection
from certiflow.adapters.sql import group,join,project

def test_fault_mutators_change_hashes():
    nodes=[join("j","a","b",(("id","id"),)),group("g","j",("region",),{"n":"count(*)"}),project("p","g",{"id":"id"})];muts=[mutate_join_key(nodes[0]),mutate_group_grain(nodes[1]),mutate_projection(nodes[2])];assert all(a.hash!=b.hash for a,b in zip(nodes,muts))
