from __future__ import annotations
from typing import Mapping, Sequence
from ..model import IRNode

def scan(name, schema: Mapping[str,str], engine="generic"): return IRNode("Scan",name,{"schema":dict(schema)},engine=engine,source_ref=name)
def project(name, source, mapping: Mapping[str,str], engine="generic"): return IRNode("Project",name,{"mapping":dict(mapping)},(source,),engine)
def filter_(name, source, predicate, engine="generic"): return IRNode("Filter",name,{"predicate":predicate},(source,),engine)
def join(name,left,right,equi: Sequence[tuple[str,str]],join_type="inner",engine="generic"): return IRNode("Join",name,{"join_type":join_type,"equi":tuple(equi)},(left,right),engine)
def group(name,source,group_by: Sequence[str],aggregates: Mapping[str,str],engine="generic"): return IRNode("Group",name,{"group_by":tuple(group_by),"aggregates":dict(aggregates)},(source,),engine)
