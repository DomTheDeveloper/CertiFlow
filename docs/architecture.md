# CertiFlow architecture

CertiFlow separates certificate production from certificate acceptance.

1. Adapters normalize dbt, SQL, and database catalog state into an engine-neutral relational IR.
2. Trusted seed facts are introduced only from explicitly configured evidence sources such as catalog keys and schema metadata.
3. Producers may use static analysis, database metadata, theorem provers, runtime observations, or AI-assisted tools to emit candidate certificates.
4. Certificates identify the exact IR subject by content hash and list all trusted assumptions used by the rule.
5. A deterministic checker validates the witness and emits `ACCEPT`, `REJECT`, or `UNKNOWN`.
6. Accepted claims enter a content-addressed fact store with dependency edges.
7. Graph changes and fact changes invalidate only downstream evidence that depends on the changed state.
8. Deployment policy gates consume accepted facts, and verification events may be written to a hash-chained audit ledger.

The trusted computing base is deliberately smaller than the evidence-producing ecosystem: canonical serialization and hashing, trusted adapter semantics, registered checker rules, and fact-dependency invalidation. Producers, generated code, LLM output, benchmark generators, and external solvers are outside the trust boundary.
