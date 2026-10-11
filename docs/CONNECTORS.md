# Connectors

Connectors implement `SourceConnector` (`src/org_brain/connectors/base.py`).

## Required declarations

- `connector_id`, version, source type
- Capabilities: enumerate, fetch, incremental, webhooks, historical, read/write
- Auth method, scopes, rate limits, health check

## Built-ins

| ID | Purpose |
|---|---|
| `git.local` | Local filesystem/git trees |
| `git.remote` | Clone/fetch remote git (optional) |
| `docs.markdown` | Markdown documentation |
| `issues.local` | Fixture/local issue records |
| `otel.http` | Observability HTTP adapter |
| `deploy.local` | Deployment metadata fixtures |
| `db.metadata` | Read-only schema metadata (allowlisted) |
| `mcp.generic` | MCP server adapter with tool allowlist |

MCP tool descriptions are untrusted and cannot expand permissions.
