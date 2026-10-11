# Security

## Reporting

Report vulnerabilities privately to the maintainers. Do not open public issues for exploitable flaws.

## Principles

- Query-time ACL enforcement
- Secrets never in prompts, embeddings, graph attributes, or logs
- Untrusted content isolation (repos, issues, MCP)
- Read-only by default; destructive actions require explicit policy
- Tenant isolation in the data-access layer
