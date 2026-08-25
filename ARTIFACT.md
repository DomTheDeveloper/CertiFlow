# CertiFlow reproducibility artifact

This repository accompanies the PVLDB 2027 Regular Research submission **“CertiFlow: Proof-Carrying Data Pipelines for Composable Transformation Assurance.”**

## Environment

The verifier and benchmark code require Python 3.9 or newer. The core runtime uses only the Python standard library. `pytest` is required only for the test suite.

```bash
python -m pip install -e .
python -m pip install pytest
```

## Functional verification

```bash
python -m pytest -q
```

The submission revision contains 27 tests spanning rule semantics, fact invalidation, graph/cache behavior, dbt and SQL normalization, live SQLite metadata, CLI behavior, deployment policy, audit chaining, and end-to-end verification.

## Experiments

Semantic mutation study:

```bash
python -m certiflow.bench.evaluate --trials 100
```

The certificate is re-bound to each mutated node hash before checking, so the experiment exercises semantic rule validation rather than stale-hash detection.

Positive-path composition:

```bash
python -m certiflow.bench.coverage --nodes 1000
```

Repeated graph scaling:

```bash
python -m certiflow.bench.suite --repeats 7
```

Selective invalidation:

```bash
python -m certiflow.bench.branched --branches 20 --depth 100 --repeats 7
python -m certiflow.bench.branched --branches 50 --depth 100 --repeats 7
```

Pinned real dbt corpus:

```bash
python -m certiflow.bench.jaffle
```

The Jaffle evaluation uses dbt Labs’ public `jaffle-shop` repository at commit `7d0d8de2d58edae06f0724a3892da0224bbf0f4a`. The runner verifies the Git blob SHA of every downloaded SQL model before processing it.

## Live database integration

The test suite creates a real temporary SQLite database, extracts primary and unique-key evidence through catalog introspection, normalizes a left-join query, and verifies the resulting fanout certificate using the recovered uniqueness fact.

## Paper build

GitHub Actions downloads the official PVLDB template bundle, including the pinned `acmart.cls` v2.19, and compiles the manuscript from `paper/`. This prevents accidental dependence on a locally installed ACM class version.

## Interpretation

`results/reference_results.json` records the measurements used in the manuscript. Absolute timings are environment-dependent. The 500/500 mutation result is regression evidence for the five implemented mutation families, not an estimate of production defect recall. The Jaffle experiment measures structural normalization coverage, not complete semantic proof coverage.
