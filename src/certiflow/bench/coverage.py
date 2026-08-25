from __future__ import annotations
import json
from ..engine import VerificationEngine
from .workload import synthetic_pipeline


def run_coverage(nodes: int = 1000, seed: int = 7) -> dict:
    graph, facts = synthetic_pipeline(nodes, seed)
    report = VerificationEngine().verify(graph, facts)
    return report.summary()


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--nodes", type=int, default=1000)
    p.add_argument("--seed", type=int, default=7)
    args = p.parse_args(argv)
    print(json.dumps(run_coverage(args.nodes, args.seed), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
