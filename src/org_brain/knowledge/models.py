"""SQLAlchemy ORM models for the knowledge platform."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _uuid() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("organizations.id"), index=True
    )
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    locator: Mapped[str] = mapped_column(Text, nullable=False)
    access_scope: Mapped[str] = mapped_column(String(64), default="read-only")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class SourceRevision(Base):
    __tablename__ = "source_revisions"
    __table_args__ = (UniqueConstraint("source_id", "revision", name="uq_source_revision"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    source_id: Mapped[str] = mapped_column(String(128), ForeignKey("sources.id"), index=True)
    revision: Mapped[str] = mapped_column(String(128), nullable=False)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FileRecord(Base):
    __tablename__ = "files"
    __table_args__ = (Index("ix_files_org_path", "organization_id", "path"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    source_id: Mapped[str] = mapped_column(String(128), index=True)
    revision: Mapped[str] = mapped_column(String(128), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(64))
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    parse_status: Mapped[str] = mapped_column(String(32), default="pending")
    parse_error: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="active")


class Entity(Base):
    __tablename__ = "entities"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "canonical_key", "knowledge_version_id", name="uq_entity_key_ver"
        ),
        Index("ix_entities_org_type", "organization_id", "type"),
        Index("ix_entities_org_name", "organization_id", "name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    knowledge_version_id: Mapped[str | None] = mapped_column(String(36), index=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    canonical_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    source_refs: Mapped[list[Any]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="active")
    search_text: Mapped[str | None] = mapped_column(Text)
    schema_version: Mapped[str] = mapped_column(String(16), default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Relationship(Base):
    __tablename__ = "relationships"
    __table_args__ = (
        Index("ix_rel_org_source", "organization_id", "source_entity_id"),
        Index("ix_rel_org_target", "organization_id", "target_entity_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    knowledge_version_id: Mapped[str | None] = mapped_column(String(36), index=True)
    source_entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    target_entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    evidence_refs: Mapped[list[Any]] = mapped_column(JSON, default=list)
    relationship_origin: Mapped[str] = mapped_column(String(64), default="parser_extracted")
    confidence_class: Mapped[str] = mapped_column(String(32), default="inferred")
    status: Mapped[str] = mapped_column(String(32), default="active")
    schema_version: Mapped[str] = mapped_column(String(16), default="1")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    knowledge_version_id: Mapped[str | None] = mapped_column(String(36), index=True)
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    repository_id: Mapped[str | None] = mapped_column(String(128))
    revision: Mapped[str | None] = mapped_column(String(128))
    path: Mapped[str | None] = mapped_column(Text)
    start_line: Mapped[int | None] = mapped_column(Integer)
    end_line: Mapped[int | None] = mapped_column(Integer)
    excerpt: Mapped[str | None] = mapped_column(Text)
    uri: Mapped[str | None] = mapped_column(Text)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extraction_method: Mapped[str] = mapped_column(String(64), default="parser")
    access_scope: Mapped[str] = mapped_column(String(64), default="read-only")
    schema_version: Mapped[str] = mapped_column(String(16), default="1")


class KnowledgeVersion(Base):
    __tablename__ = "knowledge_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default="building")  # building|published|failed
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    coverage: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="PENDING")
    progress: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error_summary: Mapped[str | None] = mapped_column(Text)
    knowledge_version_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MemoryRecord(Base):
    __tablename__ = "memory_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    entity_names: Mapped[list[Any]] = mapped_column(JSON, default=list)
    source_path: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(String(32), default="human_authored")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LiveObservation(Base):
    __tablename__ = "live_observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    resource: Mapped[str] = mapped_column(String(512), nullable=False)
    environment: Mapped[str] = mapped_column(String(64), default="unknown")
    metric: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deployment_revision: Mapped[str | None] = mapped_column(String(128))
    connector_id: Mapped[str] = mapped_column(String(128), default="otel.http")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    actor: Mapped[str] = mapped_column(String(256), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource: Mapped[str | None] = mapped_column(String(512))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AccessGrant(Base):
    __tablename__ = "access_grants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(128), index=True)
    principal: Mapped[str] = mapped_column(String(256), nullable=False)
    profile: Mapped[str] = mapped_column(String(64), default="repository_read")
    source_ids: Mapped[list[Any]] = mapped_column(JSON, default=list)  # empty = all enabled
