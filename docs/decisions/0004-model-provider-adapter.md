# ADR 0004: Provider-neutral model adapter

## Status

Accepted

## Decision

All LLM calls go through `org_brain.models.provider.ModelProvider`. Retrieval-only mode works without any provider configured.

## Consequences

Org chooses provider; core never depends on a single vendor API surface.
