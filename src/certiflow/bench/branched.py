from __future__ import annotations
from dataclasses import replace
import time, json, statistics
from ..adapters.sql import filter_, project, scan
from ..graph import PipelineGraph


def branched_pipeline(branches: int = 20, depth: int = 100) -> PipelineGraph:
    nodes = [scan("root", {"id": "int", "value": "decimal"})]
    for b in range(branches):
        current = "root"
        for d in range(depth):
            name = f"b{b:03d}_n{d:04d}"
            node = filter_(name, current, f"value >= {d}") if d % 2 == 0 else project(name, current, {"id": "id", "value": "value"})
            nodes.append(node)
            current = name
    return PipelineGraph.from_nodes(nodes)


def run_invalidation_benchmark(branches: int = 20, depth: int = 100, repeats: int = 7) -> dict:
    samples = []
    for _ in range(repeats):
        graph = branched_pipeline(branches, depth)
        target = f"b{branches // 2:03d}_n{depth // 2:04d}"
        mapping = dict(graph.nodes)
        node = mapping[target]
        args = dict(node.args)
        args["edited"] = True
        mapping[target] = replace(node, args=args)
        changed = PipelineGraph(mapping)
        t0 = time.perf_counter()
        changed_names = graph.diff(changed)
        affected = graph.descendants(changed_names)
        elapsed = (time.perf_counter() - t0) * 1000
        samples.append((elapsed, len(affected)))
    total = 1 + branches * depth
    return {
        "nodes": total,
        "branches": branches,
        "depth": depth,
        "affected_nodes": int(statistics.median(x[1] for x in samples)),
        "affected_fraction": statistics.median(x[1] for x in samples) / total,
        "invalidation_ms_median": statistics.median(x[0] for x in samples),
        "repeats": repeats,
    }


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--branches", type=int, default=20)
    p.add_argument("--depth", type=int, default=100)
    p.add_argument("--repeats", type=int, default=7)
    a = p.parse_args()
    print(json.dumps(run_invalidation_benchmark(a.branches, a.depth, a.repeats), indent=2, sort_keys=True))
