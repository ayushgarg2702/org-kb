# Threat Model

## Assets

- Org source code and schemas
- Credentials and connector tokens
- Knowledge graph and embeddings
- Query answers that may leak restricted data

## Threats

1. Cross-tenant data leakage
2. Unauthorized graph traversal revealing hidden nodes
3. Secret leakage into logs/prompts/embeddings
4. Prompt injection via retrieved docs/MCP
5. Connector privilege escalation (read → write)
6. Stale/poisoned indexes presented as current truth

## Mitigations

- Tenant filters in every repository query
- Re-check ACL before returning evidence
- Secret redaction pipeline
- Tool allowlists; untrusted content never becomes policy
- Separate action capabilities; disabled by default
- Versioned publication; freshness labels on observations
