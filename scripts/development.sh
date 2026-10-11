#!/usr/bin/env bash
set -euo pipefail
docker compose -f deploy/compose/docker-compose.yml up -d
pip install -e ".[dev]"
alembic upgrade head
echo "Ready. Init an instance with: org-brain init ./my-org-kb"
