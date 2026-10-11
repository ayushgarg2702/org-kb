"""Pydantic models for organization configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class OrganizationInfo(BaseModel):
    id: str
    display_name: str


class StorageConfig(BaseModel):
    database_url_env: str = "ORG_BRAIN_DATABASE_URL"
    data_directory: str = "./var/org-brain"
    retention_days: int = 365


class ModelsConfig(BaseModel):
    default_provider: str = "none"
    extraction_model_env: str = "ORG_BRAIN_EXTRACTION_MODEL"
    answer_model_env: str = "ORG_BRAIN_ANSWER_MODEL"


class RepositorySource(BaseModel):
    id: str
    path: str
    url: str | None = None
    revision: str = "HEAD"
    access_scope: str = "read-only"
    enabled: bool = True


class SourcesConfig(BaseModel):
    repositories: list[RepositorySource] = Field(default_factory=list)
    documentation: dict[str, Any] = Field(default_factory=dict)
    issue_tracker: dict[str, Any] = Field(default_factory=dict)
    observability: dict[str, Any] = Field(default_factory=dict)


class IndexingConfig(BaseModel):
    include: list[str] = Field(
        default_factory=lambda: [
            "**/*.py",
            "**/*.ts",
            "**/*.tsx",
            "**/*.js",
            "**/*.sql",
            "**/*.yaml",
            "**/*.yml",
            "**/*.md",
        ]
    )
    exclude: list[str] = Field(
        default_factory=lambda: [
            "**/node_modules/**",
            "**/.git/**",
            "**/vendor/**",
            "**/dist/**",
            "**/build/**",
            "**/*lock*",
        ]
    )


class SecurityConfig(BaseModel):
    tenant_isolation: str = "required"
    redact_secrets: bool = True
    enforce_source_permissions: bool = True
    allow_destructive_actions: bool = False


class QueryConfig(BaseModel):
    max_graph_depth: int = 3
    max_nodes: int = 50
    token_budget: int = 8000


class OrgConfig(BaseModel):
    api_version: str = "org-brain/v1"
    organization: OrganizationInfo
    storage: StorageConfig = Field(default_factory=StorageConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    connectors: dict[str, Any] = Field(default_factory=dict)
    indexing: IndexingConfig = Field(default_factory=IndexingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    query: QueryConfig = Field(default_factory=QueryConfig)

    def resolve_repo_path(self, repo: RepositorySource, instance_dir: Path) -> Path:
        p = Path(repo.path)
        if not p.is_absolute():
            p = (instance_dir / p).resolve()
        return p
