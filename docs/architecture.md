# CertiFlow architecture

CertiFlow separates certificate production from certificate acceptance.

1. Adapters normalize pipeline metadata into an engine-neutral relational IR.
2. Producers may use static analysis, database metadata, theorem provers, or other tools to emit certificates.
3. Certificates identify the exact IR node by content hash and list their assumptions.
4. A deterministic checker evaluates a small registered rule.
5. Accepted claims enter a content-addressed fact store with dependency edges.
6. Graph changes invalidate only facts and certificates reachable from changed nodes.

The trusted computing base is the canonical serializer, hash function, rule registry, checker, and fact-store invalidation logic. Producers and external data sources remain untrusted.
