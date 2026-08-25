# CertiFlow

CertiFlow is a research system for proof-carrying data pipelines. It turns semantic assumptions about data transformations into versioned, machine-checkable artifacts and admits derived guarantees only after independent deterministic verification.

The repository accompanies the PVLDB 2027 Regular Research submission **“CertiFlow: Proof-Carrying Data Pipelines for Composable Transformation Assurance.”**

## Core design

CertiFlow separates evidence production from trust:

1. adapters normalize dbt, SQL, and live catalog metadata into a small engine-neutral IR;
2. untrusted producers propose certificates bound to exact transformation hashes;
3. a deterministic checker validates rule-specific witnesses and trusted assumptions;
4. accepted facts enter a content-addressed store with explicit dependencies;
5. graph and fact dependencies support selective invalidation after changes;
6. policy gates consume only accepted facts, and audit events can be hash-chained.

Unsupported semantics remain explicit `UNKNOWN` or opaque boundaries. CertiFlow does not claim complete SQL semantics.

## Implemented rule families

- projection key preservation
- bounded join fanout from accepted uniqueness evidence
- aggregation grain
- restricted-field flow from explicit lineage
- schema compatibility
- filter key preservation
- union schema compatibility

## Integration surface

The artifact includes a dbt manifest adapter, conservative dbt/SQL normalizers, an engine-neutral catalog adapter, a live SQLite catalog adapter, a CLI, an inference/verification engine, policy gates, a hash-chained audit ledger, semantic fault injection, incremental-DAG benchmarks, and a pinned real-corpus runner for dbt Labs’ Jaffle Shop.

## Reproduce

```bash
python -m pip install -e .
python -m pip install pytest
python -m pytest -q
python -m certiflow.bench.evaluate --trials 100
python -m certiflow.bench.coverage --nodes 1000
python -m certiflow.bench.suite --repeats 7
python -m certiflow.bench.branched --branches 50 --depth 100 --repeats 7
python -m certiflow.bench.jaffle
```

The Jaffle runner pins both the upstream commit and all 13 model-file Git blob hashes before normalization.

See [`ARTIFACT.md`](ARTIFACT.md) for the evaluation protocol and [`results/reference_results.json`](results/reference_results.json) for the reported reference measurements.

## Repository layout

- `src/certiflow/` — implementation
- `src/certiflow/adapters/` — dbt, SQL, catalog, and SQLite integration
- `src/certiflow/policy/` — deployment gates and audit ledger
- `src/certiflow/bench/` — fault injection, graph benchmarks, and real-corpus evaluation
- `tests/` — unit and integration tests
- `paper/` — PVLDB manuscript source
- `results/` — reference result snapshot

## Author

Dominic Dabish  
Department of Computer Science  
San Diego State University
