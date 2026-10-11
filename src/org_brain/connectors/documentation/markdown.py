"""Markdown documentation connector."""

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


class DocsMarkdownConnector:
    connector_id = "docs.markdown"
    version = "1.0.0"
    source_type = "documentation"

    def __init__(self, root: Path | None = None) -> None:
        self.root = root

    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(enumerate=True, fetch=True, read=True, historical=True)

    def validate_config(self, config: dict[str, Any]) -> ValidationResult:
        path = config.get("path")
        if path and not Path(path).exists():
            return ValidationResult(ok=False, errors=[f"missing docs path: {path}"])
        return ValidationResult(ok=True)

    def health_check(self) -> HealthResult:
        ok = bool(self.root and self.root.exists())
        return HealthResult(ok=ok, message="ok" if ok else "docs path missing")

    def discover(self, scope: dict[str, Any] | None = None) -> DiscoveryResult:
        root = Path((scope or {}).get("path") or self.root or ".")
        docs = [p.relative_to(root).as_posix() for p in root.rglob("*.md") if p.is_file()]
        return DiscoveryResult(resources=[{"path": d} for d in docs])

    def fetch(self, resource_ref: str) -> SourceDocument:
        assert self.root is not None
        path = self.root / resource_ref
        return SourceDocument(uri=resource_ref, content=path.read_text(encoding="utf-8"))

    def changes_since(self, cursor: str | None) -> ChangeBatch:
        return ChangeBatch(changes=[], cursor=cursor)
