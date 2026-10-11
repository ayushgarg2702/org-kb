# Product Requirements — Org Brain

## Vision

Build a reusable master repository that enables an AI coding agent to construct and maintain a comprehensive, evidence-backed knowledge system for any organization.

## Deliverables

1. **Master repository** — implementation, schemas, specs, connectors, evaluation, deploy templates.
2. **Organization-specific KB** — created via `org-brain init` + bootstrap; owned by the organization.
3. **Interactive mind map and query interface** — progressive exploration, source-linked evidence.
4. **Evaluation and maintenance system** — accuracy benchmarks, incremental updates, monitoring.

## Functional goals

1. Bootstrap an organizational knowledge map from configured repositories and approved sources.
2. Discover files, symbols, APIs, schemas, infrastructure definitions, and relationships.
3. Connect information across repositories and systems.
4. Answer vague engineering questions without requiring exact file/API names.
5. Retrieve minimal, source-backed evidence.
6. Integrate external services via native and MCP connector interfaces.
7. Fine-grained permissions for repositories, resources, tools, and operations.
8. Maintain historical context (PRs, incidents, experiments, lessons).
9. Update incrementally after commits, merges, deployments, and operational events.
10. Progressive expandable graph UI.
11. Measure retrieval quality, correctness, faithfulness, latency, tokens, freshness, cost.
12. Identify gaps and ask targeted human questions.
13. Documented API for other engineering agents.

## Non-goals (initial)

- Arbitrary production changes without authorization
- Claiming complete understanding of every file
- Bypassing access controls
- Requiring fine-tuning to function
- Requiring Neo4j/OpenSearch for every org
- Treating model prose as verified fact

## Optimization order

1. Factual accuracy and evidence quality
2. Low token consumption
3. Low latency
4. Low operational cost (without sacrificing correctness thresholds)
