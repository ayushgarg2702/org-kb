"""Tenant-scoped knowledge store operations."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from org_brain.knowledge.models import (
    AccessGrant,
    AuditEvent,
    Entity,
    Evidence,
    Job,
    KnowledgeVersion,
    LiveObservation,
    MemoryRecord,
    Organization,
    Relationship,
    Source,
)


class KnowledgeStore:
    def __init__(self, session: Session, organization_id: str) -> None:
        self.session = session
        self.organization_id = organization_id

    def ensure_organization(self, display_name: str) -> Organization:
        org = self.session.get(Organization, self.organization_id)
        if org is None:
            org = Organization(id=self.organization_id, display_name=display_name)
            self.session.add(org)
            self.session.flush()
        return org

    def upsert_source(
        self, source_id: str, source_type: str, locator: str, access_scope: str = "read-only"
    ) -> Source:
        src = self.session.get(Source, source_id)
        if src is None:
            src = Source(
                id=source_id,
                organization_id=self.organization_id,
                source_type=source_type,
                locator=locator,
                access_scope=access_scope,
                enabled=True,
            )
            self.session.add(src)
        else:
            src.locator = locator
            src.access_scope = access_scope
        self.session.flush()
        return src

    def create_job(self, job_type: str) -> Job:
        job = Job(
            id=str(uuid4()),
            organization_id=self.organization_id,
            job_type=job_type,
            status="PENDING",
            progress={},
        )
        self.session.add(job)
        self.session.flush()
        return job

    def update_job(
        self,
        job: Job,
        status: str,
        progress: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        job.status = status
        if progress is not None:
            job.progress = {**(job.progress or {}), **progress}
        if error is not None:
            job.error_summary = error
        job.updated_at = datetime.now(UTC)
        self.session.flush()

    def start_knowledge_version(self) -> KnowledgeVersion:
        kv = KnowledgeVersion(
            id=str(uuid4()),
            organization_id=self.organization_id,
            status="building",
            is_current=False,
            coverage={},
        )
        self.session.add(kv)
        self.session.flush()
        return kv

    def publish_knowledge_version(self, kv: KnowledgeVersion, coverage: dict[str, Any]) -> None:
        self.session.execute(
            update(KnowledgeVersion)
            .where(
                KnowledgeVersion.organization_id == self.organization_id,
                KnowledgeVersion.is_current.is_(True),
            )
            .values(is_current=False)
        )
        kv.status = "published"
        kv.is_current = True
        kv.coverage = coverage
        kv.published_at = datetime.now(UTC)
        self.session.flush()

    def current_version(self) -> KnowledgeVersion | None:
        return self.session.scalar(
            select(KnowledgeVersion).where(
                KnowledgeVersion.organization_id == self.organization_id,
                KnowledgeVersion.is_current.is_(True),
            )
        )

    def add_entity(self, **kwargs: Any) -> Entity:
        ent = Entity(id=str(uuid4()), organization_id=self.organization_id, **kwargs)
        self.session.add(ent)
        self.session.flush()
        return ent

    def add_relationship(self, **kwargs: Any) -> Relationship:
        rel = Relationship(id=str(uuid4()), organization_id=self.organization_id, **kwargs)
        self.session.add(rel)
        self.session.flush()
        return rel

    def add_evidence(self, **kwargs: Any) -> Evidence:
        ev = Evidence(id=str(uuid4()), organization_id=self.organization_id, **kwargs)
        self.session.add(ev)
        self.session.flush()
        return ev

    def entities_for_version(self, version_id: str) -> list[Entity]:
        return list(
            self.session.scalars(
                select(Entity).where(
                    Entity.organization_id == self.organization_id,
                    Entity.knowledge_version_id == version_id,
                    Entity.status == "active",
                )
            )
        )

    def find_entities_by_name(self, version_id: str, names: list[str]) -> list[Entity]:
        if not names:
            return []
        return list(
            self.session.scalars(
                select(Entity).where(
                    Entity.organization_id == self.organization_id,
                    Entity.knowledge_version_id == version_id,
                    Entity.name.in_(names),
                    Entity.status == "active",
                )
            )
        )

    def search_entities(self, version_id: str, query: str, limit: int = 20) -> list[Entity]:
        q = f"%{query}%"
        return list(
            self.session.scalars(
                select(Entity)
                .where(
                    Entity.organization_id == self.organization_id,
                    Entity.knowledge_version_id == version_id,
                    Entity.status == "active",
                    (Entity.name.ilike(q)) | (Entity.search_text.ilike(q)),
                )
                .limit(limit)
            )
        )

    def neighbors(self, version_id: str, entity_id: str, limit: int = 50) -> list[Relationship]:
        return list(
            self.session.scalars(
                select(Relationship)
                .where(
                    Relationship.organization_id == self.organization_id,
                    Relationship.knowledge_version_id == version_id,
                    Relationship.status == "active",
                    (Relationship.source_entity_id == entity_id)
                    | (Relationship.target_entity_id == entity_id),
                )
                .limit(limit)
            )
        )

    def relationships_for_version(self, version_id: str) -> list[Relationship]:
        return list(
            self.session.scalars(
                select(Relationship).where(
                    Relationship.organization_id == self.organization_id,
                    Relationship.knowledge_version_id == version_id,
                    Relationship.status == "active",
                )
            )
        )

    def evidence_by_ids(self, ids: list[str]) -> list[Evidence]:
        if not ids:
            return []
        return list(
            self.session.scalars(
                select(Evidence).where(
                    Evidence.organization_id == self.organization_id,
                    Evidence.id.in_(ids),
                )
            )
        )

    def add_memory(self, **kwargs: Any) -> MemoryRecord:
        rec = MemoryRecord(id=str(uuid4()), organization_id=self.organization_id, **kwargs)
        self.session.add(rec)
        self.session.flush()
        return rec

    def list_memory(self, limit: int = 100) -> list[MemoryRecord]:
        return list(
            self.session.scalars(
                select(MemoryRecord)
                .where(MemoryRecord.organization_id == self.organization_id)
                .limit(limit)
            )
        )

    def add_observation(self, **kwargs: Any) -> LiveObservation:
        obs = LiveObservation(id=str(uuid4()), organization_id=self.organization_id, **kwargs)
        self.session.add(obs)
        self.session.flush()
        return obs

    def fresh_observations(self, now: datetime | None = None) -> list[LiveObservation]:
        now = now or datetime.now(UTC)
        rows = list(
            self.session.scalars(
                select(LiveObservation).where(
                    LiveObservation.organization_id == self.organization_id
                )
            )
        )
        return [r for r in rows if r.expires_at is None or r.expires_at > now]

    def audit(
        self, actor: str, action: str, resource: str | None = None, details: dict | None = None
    ) -> None:
        self.session.add(
            AuditEvent(
                id=str(uuid4()),
                organization_id=self.organization_id,
                actor=actor,
                action=action,
                resource=resource,
                details=details or {},
            )
        )

    def ensure_default_grant(self, principal: str = "*") -> None:
        existing = self.session.scalar(
            select(AccessGrant).where(
                AccessGrant.organization_id == self.organization_id,
                AccessGrant.principal == principal,
            )
        )
        if existing is None:
            self.session.add(
                AccessGrant(
                    id=str(uuid4()),
                    organization_id=self.organization_id,
                    principal=principal,
                    profile="repository_read",
                    source_ids=[],
                )
            )
            self.session.flush()
