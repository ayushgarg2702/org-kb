# Troubleshooting

| Symptom | Check |
|---|---|
| Preflight DB fail | `ORG_BRAIN_DATABASE_URL`, Compose up, migrations |
| No entities after bootstrap | Include globs, parser language support, coverage report |
| Query abstains always | Published knowledge version? ACL filters? |
| UI empty graph | API base URL, published version, org id header |
| Secrets in logs | Ensure redaction middleware; never print env values |
| Stale answers after commit | Run `org-brain sync`; check knowledge version |
