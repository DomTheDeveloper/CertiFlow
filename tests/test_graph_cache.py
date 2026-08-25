import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from dataclasses import replace
from certiflow import IRNode,PipelineGraph,GraphError
from certiflow.cache import CertificateCache
from certiflow.model import Certificate

def test_topology_descendants_and_diff():
    a=IRNode("Scan","a",{});b=IRNode("Filter","b",{},("a",));c=IRNode("Project","c",{},("b",));g=PipelineGraph.from_nodes([c,a,b]);assert g.topological_order()==["a","b","c"];assert g.descendants(["b"])=={"b","c"};b2=replace(b,args={"predicate":"x > 1"});g2=PipelineGraph.from_nodes([a,b2,c]);assert g.diff(g2)=={"b"};assert g2.descendants(g.diff(g2))=={"b","c"}

def test_cycle_rejected():
    a=IRNode("Filter","a",{},("b",));b=IRNode("Filter","b",{},("a",))
    try:PipelineGraph.from_nodes([a,b]);assert False
    except GraphError:pass

def test_certificate_cache_incremental_invalidation():
    a=IRNode("Scan","a",{});b=IRNode("Filter","b",{},("a",));c=IRNode("Project","c",{},("b",));old=PipelineGraph.from_nodes([a,b,c]);b2=replace(b,args={"predicate":"x > 1"});new=PipelineGraph.from_nodes([a,b2,c]);cache=CertificateCache();ca=Certificate(a.hash,"schema_compatible");cb=Certificate(b.hash,"filter_preserves_key");cc=Certificate(c.hash,"project_key")
    for node,cert in [(a,ca),(b,cb),(c,cc)]:cache.put(node,cert)
    affected=cache.invalidate_graph_change(old,new);assert affected=={"b","c"};assert cache.get(a)==(ca,);assert not cache.get(b);assert not cache.get(c)
