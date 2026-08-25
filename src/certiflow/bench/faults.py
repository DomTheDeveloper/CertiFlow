from __future__ import annotations
from dataclasses import replace

def mutate_join_key(node):
    if node.op!="Join": return node
    equi=tuple(tuple(x) for x in node.args.get("equi",()))
    if not equi: return node
    bad=list(equi); bad[0]=(bad[0][0],"__wrong_key__"); args=dict(node.args); args["equi"]=tuple(bad); return replace(node,args=args)
def mutate_group_grain(node):
    if node.op!="Group": return node
    args=dict(node.args); args["group_by"]=tuple(args.get("group_by",()))+("__extra_grain__",); return replace(node,args=args)
def mutate_projection(node):
    if node.op!="Project": return node
    args=dict(node.args); mapping=dict(args.get("mapping",{}))
    if mapping: mapping[next(iter(mapping))]="__wrong_source__"
    args["mapping"]=mapping; return replace(node,args=args)
MUTATORS={"join_key":mutate_join_key,"group_grain":mutate_group_grain,"projection":mutate_projection}
