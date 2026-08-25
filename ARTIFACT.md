# Reproducibility artifact

This repository accompanies the CertiFlow PVLDB 2027 Regular Research Paper submission.

## Environment

- Python 3.9 or newer
- no runtime third-party dependencies for the reference checker
- pytest is used for the test suite

## Install and run

```bash
python -m pip install -e .
python -m pytest -q
certiflow benchmark --nodes 1000
python -m certiflow.bench.evaluate --trials 100
python -m certiflow.bench.coverage --nodes 1000
python -m certiflow.bench.suite --repeats 7
python -m certiflow.bench.branched --branches 20 --depth 100
```

The artifact implements canonical content-addressed IR nodes and facts; typed certificates; a deterministic rule registry with three-valued outcomes; seven rule families; dependency-aware invalidation; DAG diffing; a certificate cache; dbt and catalog adapters; an untrusted inference producer; an end-to-end verifier; CLI; synthetic benchmarks; branched invalidation workloads; and five mutation families.

It does not claim complete SQL semantics. Unsupported cases produce `UNKNOWN` rather than an unsound guarantee.
