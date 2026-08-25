# CertiFlow

CertiFlow is a research system for proof-carrying data pipelines. It attaches versioned, machine-checkable evidence to data transformations and checks that evidence independently before a guarantee is admitted into a pipeline's trusted fact set.

The current system targets a PVLDB 2027 Regular Research Paper.

## Design

CertiFlow has four layers: an engine-neutral transformation IR; untrusted certificate producers; a small deterministic checker; and dependency-aware certificate caching and invalidation. The rule set currently covers key preservation, bounded join fanout, aggregation grain, schema compatibility, restricted-field flow, filter key preservation, and union schema compatibility. Unsupported semantics return `UNKNOWN`.

## Repository layout

- `src/certiflow/` - implementation
- `src/certiflow/adapters/` - dbt and catalog normalization
- `src/certiflow/bench/` - synthetic workloads and fault injection
- `tests/` - unit, integration, CLI, adapter, and regression tests
- `paper/` - PVLDB manuscript
- `docs/architecture.md` - trust boundary and data flow
- `ARTIFACT.md` - reproducibility instructions

## Quick start

```bash
python -m pip install -e .
python -m pytest -q
certiflow benchmark --nodes 1000
python -m certiflow.bench.evaluate --trials 100
python -m certiflow.bench.coverage --nodes 1000
python -m certiflow.bench.suite --repeats 7
```

## Research status

This is an active research prototype, not a production database correctness system. The trusted checker is deliberately small, while certificate producers may be arbitrarily complex. The current implementation makes the core semantics, incremental invalidation, adapter boundary, and evaluation harness executable without claiming completeness for arbitrary SQL.

## Author

Dominic Dabish  
Department of Computer Science  
San Diego State University
