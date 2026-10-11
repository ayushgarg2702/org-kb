# ADR 0001: PostgreSQL-first relationship graph

## Status

Accepted

## Decision

Store relationships as relational tables in PostgreSQL. Defer Neo4j/other graph DBs until multi-hop workload benchmarks justify operational cost.

## Consequences

Bounded neighbor queries via SQL; optional later adapter behind the same traversal interface.
