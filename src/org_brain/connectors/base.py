"""Shared connector contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ConnectorCapabilities:
    enumerate: bool = True
    fetch: bool = True
    incremental: bool = False
    webhooks: bool = False
    historical: bool = False
    read: bool = True
    write: bool = False


@dataclass
class HealthResult:
    ok: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)


@dataclass
class DiscoveryResult:
    resources: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SourceDocument:
    uri: str
    content: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangeBatch:
    changes: list[dict[str, Any]] = field(default_factory=list)
    cursor: str | None = None


class SourceConnector(Protocol):
    connector_id: str
    version: str
    source_type: str

    def capabilities(self) -> ConnectorCapabilities: ...

    def validate_config(self, config: dict[str, Any]) -> ValidationResult: ...

    def health_check(self) -> HealthResult: ...

    def discover(self, scope: dict[str, Any] | None = None) -> DiscoveryResult: ...

    def fetch(self, resource_ref: str) -> SourceDocument: ...

    def changes_since(self, cursor: str | None) -> ChangeBatch: ...
