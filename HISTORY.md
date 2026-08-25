# Development History

CertiFlow has been under active development during the two-week period leading up to the PVLDB 2027 Vision-paper submission cycle of August 25, 2026. This file records the research chronology; Git commit timestamps record when the repository history itself was materialized.

## August 11–18, 2026 — problem formulation

The initial research direction focused on a recurring weakness in heterogeneous data pipelines: correctness assumptions such as key preservation, join multiplicity, aggregation grain, schema compatibility, and restricted-field flow are rarely represented as portable, independently checkable artifacts. The project direction converged on a producer/checker separation inspired by proof-carrying systems, but specialized to versioned data-transformation DAGs.

## August 18–22, 2026 — certificate model and trust boundary

The design was refined around four principles:

1. certificate producers are untrusted;
2. the checker is small, deterministic, and independently testable;
3. unsupported semantics return `UNKNOWN` rather than being promoted to a guarantee;
4. accepted facts carry dependencies so schema or transformation changes can invalidate only affected downstream claims.

The first rule families selected for the reference semantics were key preservation, bounded join fanout, aggregation grain, and restricted data flow.

## August 22–25, 2026 — executable reference semantics

A dependency-free Python reference checker was implemented to make the trust boundary executable. The prototype introduced canonical content hashing, normalized IR nodes, typed facts, certificate witnesses, fact dependencies, and three-valued checking outcomes. A regression harness exercises successful composition, absence of required uniqueness evidence, and stale-certificate rejection.

## August 25, 2026 — PVLDB Vision-paper packaging

The research was organized as a PVLDB 2027 Vision submission, with the implementation positioned as preliminary evidence for the architecture rather than as a completed performance evaluation. The next implementation stage targets:

- dbt manifest/catalog ingestion;
- PostgreSQL and DuckDB schema/constraint adapters;
- a restricted dataframe normalizer;
- a small Rust checker implementation;
- content-addressed dependency invalidation across full DAGs;
- mutation-based fault injection and comparison with conventional data-quality checks.

This chronology documents the development period but does not alter or backdate Git commit metadata.
