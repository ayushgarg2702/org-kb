"""Local filesystem / git tree connector."""

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


class GitLocalConnector:
    connector_id = "git.local"
    version = "1.0.0"
    source_type = "git"

    def __init__(self, root: Path | None = None) -> None:
        self.root = root

    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(enumerate=True, fetch=True, incremental=True, read=True)

    def validate_config(self, config: dict[str, Any]) -> ValidationResult:
        path = config.get("path")
        if not path:
            return ValidationResult(ok=False, errors=["path required"])
        if not Path(path).exists():
            return ValidationResult(ok=False, errors=[f"path does not exist: {path}"])
        return ValidationResult(ok=True)

    def health_check(self) -> HealthResult:
        if self.root and self.root.exists():
            return HealthResult(ok=True, message="ok")
        return HealthResult(ok=False, message="root missing")

    def discover(self, scope: dict[str, Any] | None = None) -> DiscoveryResult:
        root = Path((scope or {}).get("path") or self.root or ".")
        files = [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()]
        return DiscoveryResult(resources=[{"path": f} for f in files[:5000]])

    def fetch(self, resource_ref: str) -> SourceDocument:
        assert self.root is not None
        path = self.root / resource_ref
        return SourceDocument(
            uri=resource_ref, content=path.read_text(encoding="utf-8", errors="replace")
        )

    def changes_since(self, cursor: str | None) -> ChangeBatch:
        return ChangeBatch(changes=[], cursor=cursor)
