"""FastAPI application factory."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from org_brain import __version__
from org_brain.auth.context import load_grants, require_cap, resolve_auth_from_headers
from org_brain.bootstrap.orchestrator import run_bootstrap, run_sync
from org_brain.bootstrap.preflight import run_preflight
from org_brain.config.loader import load_org_config
from org_brain.connectors.registry import list_connector_descriptors
from org_brain.knowledge.db import session_scope
from org_brain.knowledge.models import Job
from org_brain.knowledge.store import KnowledgeStore
from org_brain.live_data.service import refresh_live_observations
from org_brain.models.provider import get_provider
from org_brain.paths import resolve_instance_path
from org_brain.retrieval.engine import QueryEngine
from org_brain.security.redact import redact_text


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)


def _instance() -> Path:
    return resolve_instance_path(os.environ.get("ORG_BRAIN_INSTANCE"))


def create_app() -> FastAPI:
    app = FastAPI(title="Org Brain", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def auth_dep(
        x_org_id: str | None = Header(default=None),
        x_user_id: str | None = Header(default=None),
        x_profile: str | None = Header(default=None),
    ):
        headers: dict[str, str] = {}
        if x_org_id:
            headers["x-org-id"] = x_org_id
        if x_user_id:
            headers["x-user-id"] = x_user_id
        if x_profile:
            headers["x-profile"] = x_profile
        try:
            ctx = resolve_auth_from_headers(headers)
        except PermissionError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        with session_scope() as session:
            ctx = load_grants(session, ctx)
        return ctx

    @app.get("/api/v1/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "version": __version__}

    @app.get("/api/v1/capabilities")
    def capabilities() -> dict[str, Any]:
        return {"connectors": list_connector_descriptors(), "version": __version__}

    @app.get("/api/v1/preflight")
    def preflight(ctx=Depends(auth_dep)) -> dict[str, Any]:
        return run_preflight(_instance()).to_dict()

    @app.post("/api/v1/bootstrap")
    def bootstrap(ctx=Depends(auth_dep)) -> dict[str, Any]:
        try:
            require_cap(ctx, "can_read_source")
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return run_bootstrap(_instance())

    @app.post("/api/v1/sync")
    def sync(source_id: str | None = None, ctx=Depends(auth_dep)) -> dict[str, Any]:
        return run_sync(_instance(), source_id)

    @app.post("/api/v1/query")
    def query(body: QueryRequest, ctx=Depends(auth_dep)) -> dict[str, Any]:
        try:
            require_cap(ctx, "can_read_source")
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        cfg = load_org_config(_instance())
        if ctx.organization_id != cfg.organization.id:
            raise HTTPException(status_code=403, detail="Organization mismatch")
        provider = get_provider(cfg.models.default_provider)
        with session_scope() as session:
            engine = QueryEngine(
                session,
                cfg.organization.id,
                cfg,
                model=provider,
                allowed_source_ids=ctx.allowed_source_ids,
            )
            return engine.query(redact_text(body.question)).to_dict()

    @app.get("/api/v1/search")
    def search(
        q: str = Query(min_length=1), limit: int = 20, ctx=Depends(auth_dep)
    ) -> dict[str, Any]:
        cfg = load_org_config(_instance())
        with session_scope() as session:
            store = KnowledgeStore(session, cfg.organization.id)
            kv = store.current_version()
            if not kv:
                return {"results": []}
            ents = store.search_entities(kv.id, q, limit=limit)
            return {
                "results": [
                    {"id": e.id, "name": e.name, "type": e.type, "source_refs": e.source_refs}
                    for e in ents
                ]
            }

    @app.get("/api/v1/graph/overview")
    def graph_overview(ctx=Depends(auth_dep)) -> dict[str, Any]:
        cfg = load_org_config(_instance())
        with session_scope() as session:
            store = KnowledgeStore(session, cfg.organization.id)
            kv = store.current_version()
            if not kv:
                return {"nodes": [], "edges": [], "partial": True}
            repos = [e for e in store.entities_for_version(kv.id) if e.type == "repository"]
            return {
                "nodes": [
                    {"id": e.id, "label": e.name, "type": e.type, "confidence": "verified"}
                    for e in repos
                ],
                "edges": [],
                "knowledge_version_id": kv.id,
                "partial": bool(kv.coverage.get("incomplete")),
                "coverage": kv.coverage,
            }

    @app.get("/api/v1/graph/nodes/{node_id}")
    def graph_node(node_id: str, ctx=Depends(auth_dep)) -> dict[str, Any]:
        cfg = load_org_config(_instance())
        with session_scope() as session:
            store = KnowledgeStore(session, cfg.organization.id)
            kv = store.current_version()
            if not kv:
                raise HTTPException(404, "No knowledge version")
            for e in store.entities_for_version(kv.id):
                if e.id == node_id:
                    return {
                        "id": e.id,
                        "name": e.name,
                        "type": e.type,
                        "attributes": e.attributes,
                        "source_refs": e.source_refs,
                        "status": e.status,
                    }
            raise HTTPException(404, "Node not found")

    @app.get("/api/v1/graph/nodes/{node_id}/neighbors")
    def graph_neighbors(node_id: str, limit: int = 50, ctx=Depends(auth_dep)) -> dict[str, Any]:
        cfg = load_org_config(_instance())
        with session_scope() as session:
            store = KnowledgeStore(session, cfg.organization.id)
            kv = store.current_version()
            if not kv:
                raise HTTPException(404, "No knowledge version")
            rels = store.neighbors(kv.id, node_id, limit=limit)
            ids = {node_id}
            for r in rels:
                ids.add(r.source_entity_id)
                ids.add(r.target_entity_id)
            ents = {e.id: e for e in store.entities_for_version(kv.id) if e.id in ids}
            return {
                "nodes": [
                    {
                        "id": e.id,
                        "label": e.name,
                        "type": e.type,
                        "origin": "verified" if e.type in {"repository", "file"} else "inferred",
                    }
                    for e in ents.values()
                ],
                "edges": [
                    {
                        "id": r.id,
                        "source": r.source_entity_id,
                        "target": r.target_entity_id,
                        "label": r.type,
                        "origin": r.relationship_origin,
                        "confidence_class": r.confidence_class,
                    }
                    for r in rels
                ],
            }

    @app.get("/api/v1/entities/{entity_id}/evidence")
    def entity_evidence(entity_id: str, ctx=Depends(auth_dep)) -> dict[str, Any]:
        cfg = load_org_config(_instance())
        with session_scope() as session:
            store = KnowledgeStore(session, cfg.organization.id)
            kv = store.current_version()
            if not kv:
                raise HTTPException(404, "No knowledge version")
            entity = next((e for e in store.entities_for_version(kv.id) if e.id == entity_id), None)
            if not entity:
                raise HTTPException(404, "Entity not found")
            ev_ids = [
                ref.get("evidence_id") for ref in entity.source_refs or [] if ref.get("evidence_id")
            ]
            rows = store.evidence_by_ids([i for i in ev_ids if i])
            return {
                "entity_id": entity_id,
                "evidence": [
                    {
                        "id": e.id,
                        "path": e.path,
                        "start_line": e.start_line,
                        "end_line": e.end_line,
                        "excerpt": e.excerpt,
                        "repository_id": e.repository_id,
                        "revision": e.revision,
                    }
                    for e in rows
                ],
            }

    @app.get("/api/v1/jobs/{job_id}")
    def get_job(job_id: str, ctx=Depends(auth_dep)) -> dict[str, Any]:
        cfg = load_org_config(_instance())
        with session_scope() as session:
            job = session.get(Job, job_id)
            if not job or job.organization_id != cfg.organization.id:
                raise HTTPException(404, "Job not found")
            return {
                "id": job.id,
                "status": job.status,
                "progress": job.progress,
                "error_summary": job.error_summary,
                "knowledge_version_id": job.knowledge_version_id,
            }

    @app.get("/api/v1/connectors")
    def connectors(ctx=Depends(auth_dep)) -> dict[str, Any]:
        return {"connectors": list_connector_descriptors()}

    @app.post("/api/v1/live/refresh")
    def live_refresh(ctx=Depends(auth_dep)) -> dict[str, Any]:
        try:
            require_cap(ctx, "can_read_ops")
        except PermissionError:
            # allow repository_read orgs to skip; operational_read required for real ops
            if ctx.profile not in {"operational_read", "action_capable", "repository_read"}:
                raise HTTPException(status_code=403, detail="Missing ops capability") from None
        cfg = load_org_config(_instance())
        with session_scope() as session:
            count = refresh_live_observations(session, cfg.organization.id)
            return {"inserted": count}

    @app.get("/api/v1/memory")
    def memory(ctx=Depends(auth_dep)) -> dict[str, Any]:
        cfg = load_org_config(_instance())
        with session_scope() as session:
            store = KnowledgeStore(session, cfg.organization.id)
            rows = store.list_memory()
            return {
                "records": [
                    {
                        "id": m.id,
                        "category": m.category,
                        "summary": m.summary,
                        "source_path": m.source_path,
                        "verification_status": m.verification_status,
                    }
                    for m in rows
                ]
            }

    return app


app = create_app()
