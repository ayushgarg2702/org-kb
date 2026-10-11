# Org Brain

**A self-bootstrapping knowledge platform for engineering agents.**

This is the **research master repository**. It is not any company's knowledge brain.

An organization clones or installs this framework, runs `org-brain init` to create a **separate organization-owned KB instance**, configures repositories and permissions, then bootstraps an evidence-backed map of their engineering systems—with query API, progressive mind map, connectors, and continuous updates.

## Two deliverables

| Deliverable | Owner | Contents |
|---|---|---|
| **Master (this repo)** | Research / open source | Engine, schemas, specs, connectors, evaluation, deploy templates |
| **Org KB instance** | The organization | `org.yaml`, memory, indexes, graph, evaluation results |

## Quick start

```bash
# Install
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Start Postgres (recommended for production-like runs)
docker compose -f deploy/compose/docker-compose.yml up -d

# Create an organization KB instance (separate from this master repo)
org-brain init ./my-org-kb --org-id example-org --display-name "Example Org"

# Point at synthetic example sources (or your own)
export ORG_BRAIN_INSTANCE=./my-org-kb
export ORG_BRAIN_DATABASE_URL=postgresql+psycopg://orgbrain:orgbrain@localhost:5432/orgbrain
# Local quick-start without Docker:
# export ORG_BRAIN_DATABASE_URL=sqlite+pysqlite:///./my-org-kb/var/orgbrain.db

alembic upgrade head   # or: python -c "from org_brain.knowledge.db import create_all_tables; create_all_tables()" for SQLite
org-brain preflight
org-brain bootstrap
org-brain query "Make the personal dashboard load faster"
org-brain serve
```

Open the mind map at http://localhost:8000 (API) and http://localhost:5173 (UI in dev).

## Documentation

- [Product requirements](docs/PRODUCT_REQUIREMENTS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Implementation plan](docs/IMPLEMENTATION_PLAN.md)
- [Agent instructions](AGENTS.md)
- [Connectors](docs/CONNECTORS.md)
- [Evaluation](docs/EVALUATION.md)
- [Operations](docs/OPERATIONS.md)

## Design principles

- Never equate plausible inference with verified fact.
- Every material claim must be traceable to evidence.
- Enforce permissions at query time.
- Retrieve the smallest sufficient evidence set.
- Publish consistent knowledge versions; update incrementally.
- Partial maps must be labeled incomplete.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
