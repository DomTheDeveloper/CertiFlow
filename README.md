# CertiFlow

CertiFlow is a research prototype for proof-carrying data pipelines. It treats data-transformation guarantees as versioned, machine-checkable artifacts that can be independently validated and composed across heterogeneous pipeline stages.

The current PVLDB 2027 Vision-paper prototype focuses on:

- content-addressed binding between a certificate and the exact normalized transformation it describes;
- typed facts for properties such as keys, bounded join fanout, aggregation grain, and restricted data flow;
- an independent deterministic checker with `ACCEPT`, `REJECT`, and `UNKNOWN` outcomes;
- explicit dependencies between accepted facts so stale guarantees can be invalidated after schema or transformation changes;
- a small executable reference implementation intended to make the proposed trust boundary concrete and reproducible.

## Repository structure

- `src/certiflow.py` — reference IR, fact model, certificates, fact store, checker, and rule implementations.
- `tests/test_certiflow.py` — executable regression harness.
- `ARTIFACT.md` — reproducibility scope, environment, and expected outputs.
- `CITATION.cff` — citation metadata for the artifact.

## Quick start

Requires Python 3.9+ and no third-party packages.

```bash
python tests/test_certiflow.py
```

Expected output:

```text
CertiFlow reference prototype: 4/4 core checks passed
```

The same harness is executed in GitHub Actions on Python 3.9 and 3.12.

## Research status

The reference implementation is intentionally small. It is not presented as a complete production system and the current Vision paper does not report system-scale performance results from it. The next implementation stage targets dbt, PostgreSQL, DuckDB, and restricted dataframe adapters; a small Rust checker; content-addressed invalidation; and a larger fault-injection study on transformation DAGs.

## Author

Dominic Dabish  
Department of Computer Science  
San Diego State University  
San Diego, California, USA
