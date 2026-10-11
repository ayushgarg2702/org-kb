"""MCP adapter — capability discovery with tool allowlist.

MCP payloads are untrusted and cannot expand permissions.
"""

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


class McpGenericConnector:
    connector_id = "mcp.generic"
    version = "1.0.0"
    source_type = "mcp"

    def __init__(
        self, server_url: str | None = None, allowlist_tools: list[str] | None = None
    ) -> None:
        self.server_url = server_url
        self.allowlist_tools = allowlist_tools or []

    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            enumerate=True,
            fetch=True,
            read=True,
            write=False,
            webhooks=False,
            incremental=False,
        )

    def validate_config(self, config: dict[str, Any]) -> ValidationResult:
        errors = []
        if config.get("enabled") and not config.get("allowlist_tools") and not self.allowlist_tools:
            errors.append("MCP enabled but allowlist_tools is empty")
        return ValidationResult(ok=not errors, errors=errors)

    def health_check(self) -> HealthResult:
        if not self.server_url:
            return HealthResult(ok=True, message="MCP not configured")
        return HealthResult(ok=True, message="configured (runtime probe deferred)")

    def discover(self, scope: dict[str, Any] | None = None) -> DiscoveryResult:
        tools = [{"name": t, "allowed": True} for t in self.allowlist_tools]
        return DiscoveryResult(resources=tools)

    def fetch(self, resource_ref: str) -> SourceDocument:
        if resource_ref not in self.allowlist_tools:
            raise PermissionError(f"MCP tool not allowlisted: {resource_ref}")
        return SourceDocument(uri=resource_ref, content="", meta={"untrusted": True})

    def changes_since(self, cursor: str | None) -> ChangeBatch:
        return ChangeBatch(changes=[], cursor=cursor)

    def invoke_tool(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool not in self.allowlist_tools:
            raise PermissionError(f"MCP tool not allowlisted: {tool}")
        # Real MCP wire protocol can be plugged here; master ships the contract.
        return {"tool": tool, "arguments": arguments, "status": "not_connected"}
