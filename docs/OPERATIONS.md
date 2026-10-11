# Operations

## Local

```bash
docker compose -f deploy/compose/docker-compose.yml up -d
pip install -e ".[dev]"
alembic upgrade head
org-brain init ./my-org-kb
export ORG_BRAIN_INSTANCE=./my-org-kb
org-brain preflight && org-brain bootstrap && org-brain serve
```

## Backups

- Postgres: `pg_dump` of the org database
- Org KB git: commit `org.yaml`, `policies.yaml`, `memory/`
- Do not back up secrets into git

## Upgrades

1. Upgrade `org-brain` package
2. `alembic upgrade head`
3. `org-brain preflight`
4. Re-run evaluation suite

## Recovery

Keep last published `knowledge_versions` row active if a new publish fails. Resume bootstrap via `--resume <job-id>`.
