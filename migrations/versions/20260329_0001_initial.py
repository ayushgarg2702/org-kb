"""initial knowledge schema

Revision ID: 20260329_0001
Revises:
Create Date: 2026-03-29
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260329_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("display_name", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "sources",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("locator", sa.Text(), nullable=False),
        sa.Column("access_scope", sa.String(length=64)),
        sa.Column("enabled", sa.Boolean()),
        sa.Column("meta", sa.JSON()),
    )
    op.create_index("ix_sources_organization_id", "sources", ["organization_id"])
    op.create_table(
        "source_revisions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("source_id", sa.String(length=128), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("revision", sa.String(length=128), nullable=False),
        sa.Column("scanned_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("source_id", "revision", name="uq_source_revision"),
    )
    op.create_table(
        "files",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("revision", sa.String(length=128), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=64)),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer()),
        sa.Column("parse_status", sa.String(length=32)),
        sa.Column("parse_error", sa.Text()),
        sa.Column("status", sa.String(length=32)),
    )
    op.create_index("ix_files_org_path", "files", ["organization_id", "path"])
    op.create_table(
        "knowledge_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32)),
        sa.Column("is_current", sa.Boolean()),
        sa.Column("coverage", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("published_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "entities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("knowledge_version_id", sa.String(length=36)),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("canonical_key", sa.String(length=1024), nullable=False),
        sa.Column("attributes", sa.JSON()),
        sa.Column("source_refs", sa.JSON()),
        sa.Column("status", sa.String(length=32)),
        sa.Column("search_text", sa.Text()),
        sa.Column("schema_version", sa.String(length=16)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("organization_id", "canonical_key", "knowledge_version_id", name="uq_entity_key_ver"),
    )
    op.create_index("ix_entities_org_type", "entities", ["organization_id", "type"])
    op.create_index("ix_entities_org_name", "entities", ["organization_id", "name"])
    op.create_table(
        "relationships",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("knowledge_version_id", sa.String(length=36)),
        sa.Column("source_entity_id", sa.String(length=36), nullable=False),
        sa.Column("target_entity_id", sa.String(length=36), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("attributes", sa.JSON()),
        sa.Column("evidence_refs", sa.JSON()),
        sa.Column("relationship_origin", sa.String(length=64)),
        sa.Column("confidence_class", sa.String(length=32)),
        sa.Column("status", sa.String(length=32)),
        sa.Column("schema_version", sa.String(length=16)),
    )
    op.create_index("ix_rel_org_source", "relationships", ["organization_id", "source_entity_id"])
    op.create_index("ix_rel_org_target", "relationships", ["organization_id", "target_entity_id"])
    op.create_table(
        "evidence",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("knowledge_version_id", sa.String(length=36)),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("repository_id", sa.String(length=128)),
        sa.Column("revision", sa.String(length=128)),
        sa.Column("path", sa.Text()),
        sa.Column("start_line", sa.Integer()),
        sa.Column("end_line", sa.Integer()),
        sa.Column("excerpt", sa.Text()),
        sa.Column("uri", sa.Text()),
        sa.Column("observed_at", sa.DateTime(timezone=True)),
        sa.Column("extraction_method", sa.String(length=64)),
        sa.Column("access_scope", sa.String(length=64)),
        sa.Column("schema_version", sa.String(length=16)),
    )
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64)),
        sa.Column("progress", sa.JSON()),
        sa.Column("error_summary", sa.Text()),
        sa.Column("knowledge_version_id", sa.String(length=36)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "memory_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("entity_names", sa.JSON()),
        sa.Column("source_path", sa.Text()),
        sa.Column("verification_status", sa.String(length=32)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "live_observations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("resource", sa.String(length=512), nullable=False),
        sa.Column("environment", sa.String(length=64)),
        sa.Column("metric", sa.String(length=128), nullable=False),
        sa.Column("value", sa.JSON()),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("deployment_revision", sa.String(length=128)),
        sa.Column("connector_id", sa.String(length=128)),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("actor", sa.String(length=256), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource", sa.String(length=512)),
        sa.Column("details", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "access_grants",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("principal", sa.String(length=256), nullable=False),
        sa.Column("profile", sa.String(length=64)),
        sa.Column("source_ids", sa.JSON()),
    )


def downgrade() -> None:
    for table in [
        "access_grants",
        "audit_events",
        "live_observations",
        "memory_records",
        "jobs",
        "evidence",
        "relationships",
        "entities",
        "knowledge_versions",
        "files",
        "source_revisions",
        "sources",
        "organizations",
    ]:
        op.drop_table(table)
