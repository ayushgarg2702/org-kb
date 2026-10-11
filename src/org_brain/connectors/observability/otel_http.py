"""OpenTelemetry-compatible HTTP adapter (read-only stub with optional URL)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from org_brain.connectors.base import (
    ChangeBatch,
    ConnectorCapabilities,
    DiscoveryResult,
    HealthResult,
    SourceDocument,
    ValidationResult,
)


class OtelHttpConnector:
    connector_id = "otel.http"
    version = "1.0.0"
    source_type = "observability"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url

    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(enumerate=True, fetch=True, read=True, write=False)

    def validate_config(self, config: dict[str, Any]) -> ValidationResult:
        return ValidationResult(ok=True)

    def health_check(self) -> HealthResult:
        if not self.base_url:
            return HealthResult(ok=True, message="disabled/no URL — fixture mode")
        try:
            r = httpx.get(self.base_url, timeout=2.0)
            return HealthResult(ok=r.status_code < 500, message=f"status={r.status_code}")
        except Exception as exc:  # noqa: BLE001
            return HealthResult(ok=False, message=str(exc))

    def discover(self, scope: dict[str, Any] | None = None) -> DiscoveryResult:
        return DiscoveryResult(
            resources=[
                {
                    "resource": "personal_dashboard",
                    "metric": "http_server_duration_p95",
                    "observed_at": datetime.now(UTC).isoformat(),
                    "expires_at": (datetime.now(UTC) + timedelta(minutes=15)).isoformat(),
                    "value": {"ms": 420},
                    "environment": "staging",
                }
            ]
        )

    def fetch(self, resource_ref: str) -> SourceDocument:
        return SourceDocument(uri=resource_ref, content="{}", meta={"fixture": True})

    def changes_since(self, cursor: str | None) -> ChangeBatch:
        return ChangeBatch(changes=[], cursor=cursor)
