"""End-to-end acceptance against Postgres + synthetic organization."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from org_brain.bootstrap.init_instance import init_org_instance
from org_brain.bootstrap.orchestrator import run_bootstrap, run_sync
from org_brain.bootstrap.preflight import run_preflight
from org_brain.config.loader import load_org_config
from org_brain.evaluation.runner import evaluate_cases, load_cases
from org_brain.knowledge.db import reset_engine, session_scope
from org_brain.knowledge.store import KnowledgeStore
from org_brain.paths import repo_root
from org_brain.retrieval.engine import QueryEngine


@pytest.fixture()
def instance(tmp_path: Path) -> Path:
    reset_engine()
    db_path = tmp_path / "orgbrain.db"
    os.environ["ORG_BRAIN_DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"
    path = tmp_path / "acme-kb"
    init_org_instance(path, "example-org", "Example Organization", use_synthetic_sources=True)
    os.environ["ORG_BRAIN_INSTANCE"] = str(path)
    url = os.environ["ORG_BRAIN_DATABASE_URL"]
    if url.startswith("sqlite"):
        from org_brain.knowledge.db import create_all_tables

        create_all_tables(url)
    else:
        from alembic import command
        from alembic.config import Config

        cfg = Config(str(repo_root() / "alembic.ini"))
        command.upgrade(cfg, "head")
    return path


def test_init_preflight_bootstrap_query_sync_evaluate(instance: Path):
    pre = run_preflight(instance)
    assert pre.ok, pre.to_dict()

    result = run_bootstrap(instance)
    assert result["status"] == "PUBLISHED"
    assert result["coverage"]["entities"] > 0

    cfg = load_org_config(instance)
    with session_scope() as session:
        engine = QueryEngine(session, cfg.organization.id, cfg)
        answered = engine.query("Make the personal dashboard load faster.")
        names = {e["name"] for e in answered.entities}
        assert answered.status in {"answered", "partial"}
        assert (
            "user_dashboard" in names or "/api/dashboard" in names or "PersonalDashboard" in names
        )
        assert answered.evidence or answered.entities

        missing = engine.query("Why is the payments ledger failing in production region eu-west-3?")
        assert missing.status == "insufficient_evidence"

        store = KnowledgeStore(session, cfg.organization.id)
        kv1 = store.current_version()
        assert kv1 is not None
        version_1 = kv1.id

    # mutate synthetic backend and sync
    target = (
        repo_root()
        / "examples"
        / "synthetic-organization"
        / "backend-service"
        / "app"
        / "dashboard.py"
    )
    original = target.read_text(encoding="utf-8")
    try:
        target.write_text(original + "\n# touch for sync\n", encoding="utf-8")
        sync_result = run_sync(instance)
        assert sync_result["status"] == "PUBLISHED"
        with session_scope() as session:
            store = KnowledgeStore(session, cfg.organization.id)
            kv2 = store.current_version()
            assert kv2 is not None
            assert kv2.id != version_1
    finally:
        target.write_text(original, encoding="utf-8")

    cases = load_cases(repo_root() / "examples" / "expected-results" / "golden-questions.yaml")
    with session_scope() as session:
        report = evaluate_cases(session, cfg.organization.id, cfg, cases)
    # Allow partial failures on exact name sets but require abstention case
    abstain = next(r for r in report["results"] if r["id"] == "insufficient-evidence")
    assert abstain["ok"]
