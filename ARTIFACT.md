# Reproducibility Artifact

This repository is the public supplemental artifact for the CertiFlow PVLDB 2027 Vision-paper submission.

## Scope

The current artifact supports the architectural claims concerning the trusted checker boundary, content-addressed certificate subjects, typed facts, explicit dependencies, and three-valued checking semantics. It is not intended to reproduce system-scale performance results because the Vision submission does not report such measurements.

## Environment

- Python 3.9 or newer
- no third-party Python packages
- tested by GitHub Actions on Python 3.9 and 3.12

## Reproduce the current reference checks

From the repository root:

```bash
python tests/test_certiflow.py
```

Expected result:

```text
CertiFlow reference prototype: 4/4 core checks passed
```

The harness exercises:

1. acceptance of a join-fanout certificate when a matching uniqueness fact exists;
2. composition of the accepted fanout fact into an aggregation-grain check;
3. `UNKNOWN` when the required uniqueness fact for a join is absent;
4. `REJECT` when a certificate is stale because its subject hash does not match the current transformation.

The checker source also contains rule implementations for projection-based key preservation and restricted-field-flow checking.

## Trusted and untrusted components

The reference design treats certificate producers as untrusted. The trusted surface consists of canonicalization, subject hashing, rule dispatch, rule-specific witness validation, fact-store updates, and dependency tracking. A producer cannot directly insert accepted facts into the store.

## Planned extension for the full evaluation

The next implementation stage will add dbt manifest/catalog ingestion, PostgreSQL and DuckDB adapters, a restricted dataframe normalizer, a small Rust checker, content-addressed dependency invalidation across full pipeline DAGs, and mutation-based fault injection. Those components will be added to this repository if and when they become part of reported results.

## Contact

Dominic Dabish  
Department of Computer Science  
San Diego State University
