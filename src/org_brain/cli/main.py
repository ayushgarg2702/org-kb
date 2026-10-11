"""Org Brain CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path

import typer
import uvicorn
from rich import print as rprint

from org_brain.bootstrap.init_instance import init_org_instance
from org_brain.bootstrap.orchestrator import run_bootstrap, run_sync
from org_brain.bootstrap.preflight import run_preflight
from org_brain.config.loader import load_org_config
from org_brain.connectors.registry import list_connector_descriptors
from org_brain.evaluation.runner import evaluate_cases, load_cases
from org_brain.knowledge.db import session_scope
from org_brain.knowledge.store import KnowledgeStore
from org_brain.paths import repo_root, resolve_instance_path
from org_brain.retrieval.engine import QueryEngine

app = typer.Typer(
    name="org-brain", help="Org Brain — organizational knowledge platform", no_args_is_help=True
)


def _instance(instance: Path | None) -> Path:
    return resolve_instance_path(instance)


def _emit(data: object, as_json: bool) -> None:
    if as_json:
        typer.echo(json.dumps(data, indent=2, default=str))
    else:
        rprint(data)


@app.command("init")
def init_cmd(
    path: Path = typer.Argument(..., help="Target directory for the org KB instance"),
    org_id: str = typer.Option("example-org", "--org-id"),
    display_name: str = typer.Option("Example Organization", "--display-name"),
    synthetic: bool = typer.Option(True, "--synthetic/--no-synthetic"),
) -> None:
    """Create a separate organization-owned KB instance."""
    target = init_org_instance(path, org_id, display_name, use_synthetic_sources=synthetic)
    rprint(f"[green]Created org KB instance at[/green] {target}")


@app.command("preflight")
def preflight_cmd(
    instance: Path | None = typer.Option(None, "--instance", envvar="ORG_BRAIN_INSTANCE"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    report = run_preflight(_instance(instance))
    _emit(report.to_dict(), as_json)
    raise typer.Exit(0 if report.ok else 1)


@app.command("config")
def config_cmd(
    action: str = typer.Argument("validate"),
    instance: Path | None = typer.Option(None, "--instance", envvar="ORG_BRAIN_INSTANCE"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    if action != "validate":
        raise typer.BadParameter("Only 'validate' is supported")
    cfg = load_org_config(_instance(instance))
    _emit({"ok": True, "organization": cfg.organization.model_dump()}, as_json)


@app.command("bootstrap")
def bootstrap_cmd(
    instance: Path | None = typer.Option(None, "--instance", envvar="ORG_BRAIN_INSTANCE"),
    resume: str | None = typer.Option(None, "--resume"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    result = run_bootstrap(_instance(instance), resume_job_id=resume)
    _emit(result, as_json)
    raise typer.Exit(0 if result.get("status") == "PUBLISHED" else 1)


@app.command("sync")
def sync_cmd(
    instance: Path | None = typer.Option(None, "--instance", envvar="ORG_BRAIN_INSTANCE"),
    source: str | None = typer.Option(None, "--source"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    result = run_sync(_instance(instance), source)
    _emit(result, as_json)


@app.command("query")
def query_cmd(
    question: str = typer.Argument(...),
    instance: Path | None = typer.Option(None, "--instance", envvar="ORG_BRAIN_INSTANCE"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    inst = _instance(instance)
    cfg = load_org_config(inst)
    with session_scope() as session:
        resp = QueryEngine(session, cfg.organization.id, cfg).query(question)
        _emit(resp.to_dict(), as_json)


@app.command("search")
def search_cmd(
    query: str = typer.Argument(...),
    instance: Path | None = typer.Option(None, "--instance", envvar="ORG_BRAIN_INSTANCE"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    inst = _instance(instance)
    cfg = load_org_config(inst)
    with session_scope() as session:
        store = KnowledgeStore(session, cfg.organization.id)
        kv = store.current_version()
        if not kv:
            _emit({"results": []}, as_json)
            return
        ents = store.search_entities(kv.id, query)
        _emit({"results": [{"id": e.id, "name": e.name, "type": e.type} for e in ents]}, as_json)


@app.command("evaluate")
def evaluate_cmd(
    instance: Path | None = typer.Option(None, "--instance", envvar="ORG_BRAIN_INSTANCE"),
    dataset: Path | None = typer.Option(None, "--dataset"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    inst = _instance(instance)
    cfg = load_org_config(inst)
    path = dataset or (repo_root() / "examples" / "expected-results" / "golden-questions.yaml")
    cases = load_cases(path)
    with session_scope() as session:
        report = evaluate_cases(session, cfg.organization.id, cfg, cases)
    _emit(report, as_json)
    raise typer.Exit(0 if report["failed"] == 0 else 1)


@app.command("status")
def status_cmd(
    instance: Path | None = typer.Option(None, "--instance", envvar="ORG_BRAIN_INSTANCE"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    inst = _instance(instance)
    cfg = load_org_config(inst)
    with session_scope() as session:
        store = KnowledgeStore(session, cfg.organization.id)
        kv = store.current_version()
        _emit(
            {
                "organization_id": cfg.organization.id,
                "knowledge_version_id": kv.id if kv else None,
                "coverage": kv.coverage if kv else None,
                "published_at": kv.published_at if kv else None,
            },
            as_json,
        )


@app.command("connectors")
def connectors_cmd(
    action: str = typer.Argument("list"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    if action not in {"list", "health"}:
        raise typer.BadParameter("list|health")
    data = list_connector_descriptors()
    if action == "health":
        from org_brain.connectors.registry import get_connector_class

        health = []
        for d in data:
            cls = get_connector_class(d["connector_id"])
            health.append({"connector_id": d["connector_id"], **cls().health_check().__dict__})
        _emit(health, as_json)
    else:
        _emit(data, as_json)


@app.command("serve")
def serve_cmd(
    host: str = typer.Option(None, "--host"),
    port: int = typer.Option(None, "--port"),
    instance: Path | None = typer.Option(None, "--instance", envvar="ORG_BRAIN_INSTANCE"),
) -> None:
    if instance:
        os.environ["ORG_BRAIN_INSTANCE"] = str(instance.resolve())
    uvicorn.run(
        "org_brain.api.app:app",
        host=host or os.environ.get("ORG_BRAIN_HOST", "0.0.0.0"),
        port=port or int(os.environ.get("ORG_BRAIN_PORT", "8000")),
        reload=False,
    )


@app.command("sources")
def sources_cmd(
    action: str = typer.Argument("list"),
    instance: Path | None = typer.Option(None, "--instance", envvar="ORG_BRAIN_INSTANCE"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    cfg = load_org_config(_instance(instance))
    _emit([r.model_dump() for r in cfg.sources.repositories], as_json)


@app.command("memory")
def memory_cmd(
    action: str = typer.Argument("list"),
    instance: Path | None = typer.Option(None, "--instance", envvar="ORG_BRAIN_INSTANCE"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    cfg = load_org_config(_instance(instance))
    with session_scope() as session:
        store = KnowledgeStore(session, cfg.organization.id)
        rows = store.list_memory()
        _emit(
            [{"id": m.id, "category": m.category, "summary": m.summary} for m in rows],
            as_json,
        )


if __name__ == "__main__":
    app()
