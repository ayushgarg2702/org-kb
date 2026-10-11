"""Read-only database metadata connector (allowlisted tables)."""

from __future__ import annotations

from typing import Any

from org_brain.connectors.base import (
    ChangeBatch,
    ConnectorCapabilities,
    DiscoveryResult,
    HealthResult,
    SourceDocument,
    ValidationResult,
)


class DbMetadataConnector:
    connector_id = "db.metadata"
    version = "1.0.0"
    source_type = "database"

    def __init__(self, allowlist_tables: list[str] | None = None) -> None:
        self.allowlist_tables = allowlist_tables or []

    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(enumerate=True, fetch=True, read=True, write=False)

    def validate_config(self, config: dict[str, Any]) -> ValidationResult:
        if config.get("enabled") and not config.get("allowlist_tables", self.allowlist_tables):
            return ValidationResult(ok=False, errors=["allowlist_tables required when enabled"])
        return ValidationResult(ok=True)

    def health_check(self) -> HealthResult:
        return HealthResult(ok=True, message="metadata-only; no live DB required for contract")

    def discover(self, scope: dict[str, Any] | None = None) -> DiscoveryResult:
        return DiscoveryResult(resources=[{"table": t} for t in self.allowlist_tables])

    def fetch(self, resource_ref: str) -> SourceDocument:
        if resource_ref not in self.allowlist_tables:
            raise PermissionError(f"table not allowlisted: {resource_ref}")
        return SourceDocument(uri=resource_ref, content="", meta={"read_only": True})

    def changes_since(self, cursor: str | None) -> ChangeBatch:
        return ChangeBatch(changes=[], cursor=cursor)
