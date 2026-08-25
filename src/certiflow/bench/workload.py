from __future__ import annotations
import random
from ..adapters.sql import filter_,group,join,project,scan
from ..graph import PipelineGraph
from ..model import Fact

def synthetic_pipeline(size:int=100,seed:int=7)->tuple[PipelineGraph,list[Fact]]:
    if size<3:raise ValueError("size must be >= 3")
    rng=random.Random(seed);nodes=[scan("customers",{"customer_id":"int","region":"text"}),scan("orders",{"order_id":"int","customer_id":"int","amount":"decimal"})];facts=[Fact.make("Key","customers",{"columns":("customer_id",)}),Fact.make("Key","orders",{"columns":("order_id",)})];current="orders"
    for i in range(size-2):
        name=f"n{i:04d}";kind=i%4
        if kind==0:node=filter_(name,current,f"amount >= {rng.randrange(0,100)}")
        elif kind==1:node=project(name,current,{"order_id":"order_id","customer_id":"customer_id","amount":"amount"})
        elif kind==2 and i<size-4:node=join(name,current,"customers",(("customer_id","customer_id"),),"left")
        else:node=group(name,current,("customer_id",),{"amount_sum":"sum(amount)"})
        nodes.append(node);current=name
    return PipelineGraph.from_nodes(nodes),facts
