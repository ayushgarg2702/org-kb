# Implementation Plan

Phases 0–8 with exit gates. See repository root plan and `specs/acceptance-criteria.md`.

| Phase | Focus | Exit gate |
|---|---|---|
| 0 | Specs, schemas, skeleton, CI | Validation commands run without guessing |
| 1 | Init, preflight, inventory, parsers, jobs | Synthetic scan reproducible; failures visible |
| 2 | Postgres knowledge + versioned publish | Provenance-complete queries |
| 3 | Adaptive retrieval + Q&A | Golden questions + abstention |
| 4 | Graph API + mind map UI | Progressive expand with evidence |
| 5 | History + engineering memory | History ≠ current state |
| 6 | Incremental sync + live observations | Consistent versions; TTL on live data |
| 7 | Connectors + MCP | New connector without core rewrite |
| 8 | Production hardening | Security + ops acceptance |

Each phase produces runnable code, tests, docs, and a milestone report per `AGENTS.md`.
