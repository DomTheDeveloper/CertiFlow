from __future__ import annotations
import argparse, json
from pathlib import Path
from .adapters.dbt import DbtManifestAdapter
from .adapters.sqlite import SQLiteAdapter
from .bench.runner import run_incremental_benchmark
from .checker import Checker
from .graph import PipelineGraph
from .model import Certificate, Fact, IRNode, Verdict
from .serde import cert_from_dict, load_json, node_from_dict
from .sqlnorm import normalize_select


def cmd_benchmark(args) -> int:
    result = run_incremental_benchmark(args.nodes, args.seed, args.position)
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    return 0


def cmd_dbt_summary(args) -> int:
    adapter = DbtManifestAdapter.from_path(args.manifest)
    nodes = list(adapter.nodes())
    graph = PipelineGraph.from_nodes(nodes)
    print(json.dumps({
        "nodes": len(nodes),
        "topological_order_head": graph.topological_order()[:10],
        "seed_facts": [f.as_dict() for f in adapter.seed_facts()],
    }, indent=2, sort_keys=True))
    return 0



def cmd_sqlite_summary(args) -> int:
    adapter = SQLiteAdapter.from_path(args.database)
    try:
        nodes = list(adapter.nodes())
        facts = list(adapter.seed_facts())
    finally:
        adapter.close()
    print(json.dumps({
        "nodes": [n.canonical() for n in nodes],
        "seed_facts": [f.as_dict() for f in facts],
    }, indent=2, sort_keys=True))
    return 0


def cmd_normalize_sql(args) -> int:
    sql = Path(args.file).read_text(encoding="utf-8") if args.file else args.sql
    nodes = normalize_select(sql, name=args.name, engine=args.engine)
    print(json.dumps([n.canonical() for n in nodes], indent=2, sort_keys=True))
    return 0


def cmd_verify(args) -> int:
    payload = load_json(args.input)
    node = node_from_dict(payload["node"])
    checker = Checker()
    for f in payload.get("facts", ()):
        checker.store.add(Fact.make(f["kind"], f["subject"], f.get("payload", {}),
                                    f.get("deps", ()), f.get("strength", "invariant")))
    cert = cert_from_dict(payload["certificate"])
    result = checker.verify(node, cert)
    print(json.dumps({
        "verdict": result.verdict.value,
        "reason": result.reason,
        "claims": [f.as_dict() for f in result.claims],
        "certificate_id": result.certificate_id,
    }, indent=2, sort_keys=True))
    return 0 if result.verdict == Verdict.ACCEPT else 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="certiflow", description="Proof-carrying data pipeline verifier")
    sub = p.add_subparsers(dest="command", required=True)
    b = sub.add_parser("benchmark", help="run incremental graph benchmark")
    b.add_argument("--nodes", type=int, default=1000)
    b.add_argument("--seed", type=int, default=7)
    b.add_argument("--position", type=float, default=0.5)
    b.set_defaults(func=cmd_benchmark)
    d = sub.add_parser("dbt-summary", help="normalize a dbt manifest")
    d.add_argument("manifest")
    d.set_defaults(func=cmd_dbt_summary)
    sq = sub.add_parser("sqlite-summary", help="inspect live SQLite schema and key facts")
    sq.add_argument("database")
    sq.set_defaults(func=cmd_sqlite_summary)
    ns = sub.add_parser("normalize-sql", help="normalize the supported SELECT subset to IR")
    source = ns.add_mutually_exclusive_group(required=True)
    source.add_argument("--sql")
    source.add_argument("--file")
    ns.add_argument("--name", default="query")
    ns.add_argument("--engine", default="sql")
    ns.set_defaults(func=cmd_normalize_sql)
    v = sub.add_parser("verify", help="verify one JSON node/certificate bundle")
    v.add_argument("input")
    v.set_defaults(func=cmd_verify)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
