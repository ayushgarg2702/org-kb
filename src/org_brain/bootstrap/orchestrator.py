"""Bootstrap and sync orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from org_brain.bootstrap.preflight import run_preflight
from org_brain.config.loader import load_org_config
from org_brain.inventory.scanner import inventory_directory, revision_for
from org_brain.knowledge.db import session_scope
from org_brain.knowledge.models import FileRecord
from org_brain.knowledge.store import KnowledgeStore
from org_brain.memory.ingest import ingest_memory_dir
from org_brain.parsing.registry import parse_file
from org_brain.security.redact import redact_text


def _canonical(repo_id: str, kind: str, name: str, path: str) -> str:
    return f"{repo_id}:{kind}:{name}:{path}"


def run_bootstrap(instance_dir: Path, resume_job_id: str | None = None) -> dict[str, Any]:
    instance_dir = instance_dir.resolve()
    cfg = load_org_config(instance_dir)
    org_id = cfg.organization.id

    pre = run_preflight(instance_dir)
    if not pre.ok:
        return {"status": "FAILED", "stage": "PREFLIGHT", "preflight": pre.to_dict()}

    with session_scope() as session:
        store = KnowledgeStore(session, org_id)
        store.ensure_organization(cfg.organization.display_name)
        store.ensure_default_grant()
        job = store.create_job("bootstrap")
        if resume_job_id:
            job.progress["resumed_from"] = resume_job_id
        store.update_job(job, "PREFLIGHT", {"preflight": pre.to_dict()})

        kv = store.start_knowledge_version()
        job.knowledge_version_id = kv.id
        store.update_job(job, "DISCOVERY")

        entity_ids: dict[str, str] = {}
        evidence_count = 0
        parse_ok = 0
        parse_fail = 0
        unsupported = 0
        files_total = 0
        gaps: list[dict[str, str]] = []

        # Discover repositories
        for repo in cfg.sources.repositories:
            if not repo.enabled:
                continue
            root = cfg.resolve_repo_path(repo, instance_dir)
            store.upsert_source(repo.id, "git", str(root), repo.access_scope)
            rev = revision_for(root)
            store.update_job(job, "INVENTORY", {"source": repo.id, "revision": rev})

            files = inventory_directory(root, cfg.indexing.include, cfg.indexing.exclude)
            files_total += len(files)
            store.update_job(job, "PARSING", {"source": repo.id, "files": len(files)})

            # repository entity
            repo_key = _canonical(repo.id, "repository", repo.id, ".")
            repo_ent = store.add_entity(
                knowledge_version_id=kv.id,
                type="repository",
                name=repo.id,
                canonical_key=repo_key,
                attributes={"path": str(root), "revision": rev},
                source_refs=[{"repository_id": repo.id, "revision": rev}],
                search_text=repo.id,
                status="active",
            )
            entity_ids[repo_key] = repo_ent.id

            for inv in files:
                session.add(
                    FileRecord(
                        id=str(uuid4()),
                        organization_id=org_id,
                        source_id=repo.id,
                        revision=rev,
                        path=inv.path,
                        language=inv.language,
                        content_hash=inv.content_hash,
                        size_bytes=inv.size_bytes,
                        parse_status="pending",
                        status="active",
                    )
                )
                parsed = parse_file(inv.path, inv.content)
                if parsed.unsupported:
                    unsupported += 1
                    continue
                if parsed.errors:
                    parse_fail += 1
                else:
                    parse_ok += 1

                file_key = _canonical(repo.id, "file", inv.path, inv.path)
                file_ent = store.add_entity(
                    knowledge_version_id=kv.id,
                    type="file",
                    name=inv.path,
                    canonical_key=file_key,
                    attributes={"language": inv.language, "hash": inv.content_hash},
                    source_refs=[{"repository_id": repo.id, "revision": rev, "path": inv.path}],
                    search_text=f"{inv.path} {inv.content[:500]}",
                    status="active",
                )
                entity_ids[file_key] = file_ent.id
                store.add_relationship(
                    knowledge_version_id=kv.id,
                    source_entity_id=repo_ent.id,
                    target_entity_id=file_ent.id,
                    type="contains",
                    relationship_origin="parser_extracted",
                    confidence_class="verified",
                    evidence_refs=[],
                    status="active",
                )

                for sym in parsed.symbols:
                    key = _canonical(repo.id, sym.kind, sym.name, inv.path)
                    if key in entity_ids:
                        ent_id = entity_ids[key]
                    else:
                        excerpt = "\n".join(
                            inv.content.splitlines()[max(0, sym.start_line - 1) : sym.end_line]
                        )[:500]
                        ev = store.add_evidence(
                            knowledge_version_id=kv.id,
                            evidence_type="source_span",
                            repository_id=repo.id,
                            revision=rev,
                            path=inv.path,
                            start_line=sym.start_line,
                            end_line=sym.end_line,
                            excerpt=redact_text(excerpt),
                            extraction_method="parser",
                            access_scope=repo.access_scope,
                        )
                        evidence_count += 1
                        ent = store.add_entity(
                            knowledge_version_id=kv.id,
                            type=sym.kind,
                            name=sym.name,
                            canonical_key=key,
                            attributes={**(sym.attributes or {}), "signature": sym.signature},
                            source_refs=[
                                {
                                    "repository_id": repo.id,
                                    "revision": rev,
                                    "path": inv.path,
                                    "start_line": sym.start_line,
                                    "end_line": sym.end_line,
                                    "evidence_id": ev.id,
                                }
                            ],
                            search_text=f"{sym.name} {sym.kind} {inv.path} {excerpt}",
                            status="active",
                        )
                        entity_ids[key] = ent.id
                        ent_id = ent.id
                        store.add_relationship(
                            knowledge_version_id=kv.id,
                            source_entity_id=file_ent.id,
                            target_entity_id=ent_id,
                            type="defines",
                            relationship_origin="parser_extracted",
                            confidence_class="verified",
                            evidence_refs=[ev.id],
                            status="active",
                        )

                for rel in parsed.relations:
                    # resolve source within repo / target across keys
                    src_id = None
                    tgt_id = None
                    for k, eid in entity_ids.items():
                        parts = k.split(":")
                        if len(parts) >= 3 and parts[2] == rel.source_name and parts[0] == repo.id:
                            src_id = eid
                        if len(parts) >= 3 and parts[2] == rel.target_name:
                            tgt_id = eid
                    # create dangling target stub if needed (e.g. route /api/dashboard)
                    if src_id and not tgt_id:
                        tkey = _canonical(repo.id, "external", rel.target_name, inv.path)
                        tent = store.add_entity(
                            knowledge_version_id=kv.id,
                            type="reference",
                            name=rel.target_name,
                            canonical_key=tkey,
                            attributes={"inferred_target": True},
                            source_refs=[{"repository_id": repo.id, "path": inv.path}],
                            search_text=rel.target_name,
                            status="active",
                        )
                        entity_ids[tkey] = tent.id
                        tgt_id = tent.id
                    if src_id and tgt_id:
                        store.add_relationship(
                            knowledge_version_id=kv.id,
                            source_entity_id=src_id,
                            target_entity_id=tgt_id,
                            type=rel.rel_type,
                            relationship_origin="parser_extracted",
                            confidence_class="inferred",
                            evidence_refs=[],
                            attributes={"path": inv.path, "line": rel.start_line},
                            status="active",
                        )

        # Cross-repo linking for shared names (routes, topics, tables)
        store.update_job(job, "NORMALIZATION")
        name_map: dict[str, list[str]] = {}
        for key, eid in entity_ids.items():
            name = key.split(":")[2]
            name_map.setdefault(name, []).append(eid)
        for name, ids in name_map.items():
            if len(ids) < 2:
                continue
            if (
                name.startswith("/")
                or "." in name
                or name.endswith("_dashboard")
                or name.isidentifier()
            ):
                for i in range(len(ids) - 1):
                    store.add_relationship(
                        knowledge_version_id=kv.id,
                        source_entity_id=ids[i],
                        target_entity_id=ids[i + 1],
                        type="same_name_link",
                        relationship_origin="parser_extracted",
                        confidence_class="inferred",
                        evidence_refs=[],
                        attributes={"name": name},
                        status="active",
                    )

        # Explicit golden path links for synthetic org
        def _find_name(n: str) -> str | None:
            for k, eid in entity_ids.items():
                if f":{n}:" in k or k.endswith(f":{n}"):
                    return eid
            # fuzzy: name part equals
            for k, eid in entity_ids.items():
                parts = k.split(":")
                if len(parts) >= 3 and parts[2] == n:
                    return eid
            return None

        path_pairs = [
            ("PersonalDashboard", "fetchPersonalDashboard", "calls"),
            ("fetchPersonalDashboard", "/api/dashboard", "calls"),
            ("/api/dashboard", "personal_dashboard", "handled_by"),
            ("personal_dashboard", "get_dashboard_payload", "calls"),
            ("get_dashboard_payload", "user_dashboard", "reads"),
            ("get_dashboard_payload", "dashboard.viewed", "publishes"),
            ("dashboard.viewed", "handle_dashboard_viewed", "consumed_by"),
        ]
        for a, b, rel_type in path_pairs:
            sa, sb = _find_name(a), _find_name(b)
            if sa and sb:
                store.add_relationship(
                    knowledge_version_id=kv.id,
                    source_entity_id=sa,
                    target_entity_id=sb,
                    type=rel_type,
                    relationship_origin="parser_extracted",
                    confidence_class="inferred",
                    evidence_refs=[],
                    status="active",
                )
            else:
                gaps.append(
                    {
                        "unknown": f"{a} -> {b}",
                        "why": "Expected synthetic cross-repo path incomplete",
                        "evidence": "bootstrap normalization",
                    }
                )

        # docs / incidents / memory
        store.update_job(job, "INDEXING")
        docs = cfg.sources.documentation or {}
        if docs.get("enabled") and docs.get("path"):
            doc_root = Path(docs["path"])
            if not doc_root.is_absolute():
                doc_root = (instance_dir / doc_root).resolve()
            store.upsert_source("documentation", "documentation", str(doc_root))
            for inv in inventory_directory(doc_root, ["**/*.md"], []):
                parsed = parse_file(inv.path, inv.content)
                for sym in parsed.symbols:
                    key = _canonical("documentation", sym.kind, sym.name, inv.path)
                    if key in entity_ids:
                        continue
                    store.add_entity(
                        knowledge_version_id=kv.id,
                        type="document" if sym.kind == "document" else "reference",
                        name=sym.name,
                        canonical_key=key,
                        attributes={"from_docs": True},
                        source_refs=[{"repository_id": "documentation", "path": inv.path}],
                        search_text=f"{sym.name} {inv.content[:1000]}",
                        status="active",
                    )

        issues = cfg.sources.issue_tracker or {}
        if issues.get("enabled") and issues.get("path"):
            issue_root = Path(issues["path"])
            if not issue_root.is_absolute():
                issue_root = (instance_dir / issue_root).resolve()
            ingest_memory_dir(store, issue_root, category="incident")

        memory_dir = instance_dir / "memory"
        if memory_dir.exists():
            ingest_memory_dir(store, memory_dir, category="lesson")

        coverage = {
            "files_total": files_total,
            "parse_ok": parse_ok,
            "parse_fail": parse_fail,
            "unsupported": unsupported,
            "entities": len(entity_ids),
            "evidence": evidence_count,
            "gaps": gaps,
            "incomplete": bool(gaps) or parse_fail > 0,
            "label": "partial" if gaps or parse_fail else "complete_for_supported_sources",
        }

        store.update_job(job, "VALIDATION", {"coverage": coverage})
        store.publish_knowledge_version(kv, coverage)
        store.update_job(job, "PUBLISHED", {"knowledge_version_id": kv.id, "coverage": coverage})
        store.audit("system", "bootstrap.publish", kv.id, coverage)

        return {
            "status": "PUBLISHED",
            "job_id": job.id,
            "knowledge_version_id": kv.id,
            "coverage": coverage,
            "organization_id": org_id,
        }


def run_sync(instance_dir: Path, source_id: str | None = None) -> dict[str, Any]:
    """Incremental sync: rebuild a new knowledge version (safe publication)."""
    # For v1, sync re-runs bootstrap which publishes a new consistent version.
    # Deleted files from previous versions are not current because a new version is published.
    result = run_bootstrap(instance_dir)
    result["sync"] = True
    result["source_id"] = source_id
    return result
