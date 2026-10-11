# Architecture

## Product split

```
Master repo (engine + contracts)
        |
        v
org-brain init  -->  Org KB instance (config, memory, policies)
        |
        v
org-brain bootstrap  -->  Postgres knowledge versions + indexes
        |
        +--> Query API / Mind map / Agents
```

## Logical modules

Configuration, bootstrap, connectors, inventory, code intelligence, entity catalog, relationship/evidence store, lexical/symbol/vector indexes, query planning, engineering memory, live data, auth/audit, API, graph UI, evaluation, jobs, telemetry.

Start as a modular monolith; split workers only when justified.

## Storage

| Concern | Store |
|---|---|
| Entities, relationships, evidence, jobs, ACL | PostgreSQL |
| Lexical search | Postgres FTS |
| Symbols | Postgres tables |
| Vectors | pgvector (optional) |
| Human memory | Org instance Markdown/YAML + indexed rows |
| Live observations | Bounded cache with TTL |

Graph DB deferred until benchmarks justify it (ADR 0001).

## Query pipeline

Authenticate → classify intent → exact/symbol → lexical/semantic → bounded graph → history → live (if needed) → verify ACL/freshness → answer or abstain.

## Ingestion pipeline

Connectors → inventory/diff → parse/extract → normalize → validate → publish knowledge version.

## Security

Tenant isolation in data layer; query-time ACL; secrets never indexed; untrusted content isolation; read-only default.
