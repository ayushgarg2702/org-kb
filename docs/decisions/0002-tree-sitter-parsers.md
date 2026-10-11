# ADR 0002: Tree-sitter for code parsing

## Status

Accepted

## Decision

Use Tree-sitter with language grammars for structural extraction. Supplement with language-specific heuristics for routes/schema refs. Record parse failures explicitly.

## Consequences

Deterministic structure where grammar supports it; capability-aware coverage reports.
