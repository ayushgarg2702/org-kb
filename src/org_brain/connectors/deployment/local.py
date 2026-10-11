"""Local deployment metadata connector (manifests / fixtures)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from org_brain.connectors.base import (
    ChangeBatch,
    ConnectorCapabilities,
    DiscoveryResult,
    HealthResult,
    SourceDocument,
    ValidationResult,
)


class DeployLocalConnector:
    connector_id = "deploy.local"
    version = "1.0.0"
    source_type = "deployment"

    def __init__(self, root: Path | None = None) -> None:
        self.root = root

    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(enumerate=True, fetch=True, read=True)

    def validate_config(self, config: dict[str, Any]) -> ValidationResult:
        return ValidationResult(ok=True)

    def health_check(self) -> HealthResult:
        return HealthResult(ok=True, message="ok")

    def discover(self, scope: dict[str, Any] | None = None) -> DiscoveryResult:
        root = Path((scope or {}).get("path") or self.root or ".")
        if not root.exists():
            return DiscoveryResult()
        files = [p.relative_to(root).as_posix() for p in root.rglob("*.yaml")]
        return DiscoveryResult(resources=[{"path": f, "kind": "manifest"} for f in files])

    def fetch(self, resource_ref: str) -> SourceDocument:
        assert self.root is not None
        path = self.root / resource_ref
        return SourceDocument(uri=resource_ref, content=path.read_text(encoding="utf-8"))

    def changes_since(self, cursor: str | None) -> ChangeBatch:
        return ChangeBatch(changes=[], cursor=cursor)
