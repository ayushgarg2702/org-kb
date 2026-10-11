"""Connector registry."""

from __future__ import annotations

from typing import Any

from org_brain.connectors.database.metadata import DbMetadataConnector
from org_brain.connectors.deployment.local import DeployLocalConnector
from org_brain.connectors.documentation.markdown import DocsMarkdownConnector
from org_brain.connectors.git.local import GitLocalConnector
from org_brain.connectors.issue_tracking.local import IssuesLocalConnector
from org_brain.connectors.mcp.adapter import McpGenericConnector
from org_brain.connectors.observability.otel_http import OtelHttpConnector


def builtin_connectors() -> dict[str, Any]:
    return {
        GitLocalConnector.connector_id: GitLocalConnector,
        DocsMarkdownConnector.connector_id: DocsMarkdownConnector,
        IssuesLocalConnector.connector_id: IssuesLocalConnector,
        OtelHttpConnector.connector_id: OtelHttpConnector,
        McpGenericConnector.connector_id: McpGenericConnector,
        DeployLocalConnector.connector_id: DeployLocalConnector,
        DbMetadataConnector.connector_id: DbMetadataConnector,
    }


def get_connector_class(connector_id: str) -> type[Any]:
    registry = builtin_connectors()
    if connector_id not in registry:
        raise KeyError(f"Unknown connector: {connector_id}")
    return registry[connector_id]  # type: ignore[no-any-return]


def list_connector_descriptors() -> list[dict[str, Any]]:
    out = []
    for cid, cls in builtin_connectors().items():
        inst = cls()
        caps = inst.capabilities()
        out.append(
            {
                "connector_id": getattr(inst, "connector_id", cid),
                "version": getattr(inst, "version", "1.0.0"),
                "source_type": getattr(inst, "source_type", "unknown"),
                "capabilities": caps.__dict__,
            }
        )
    # dedupe by connector_id
    seen: set[str] = set()
    unique = []
    for item in out:
        if item["connector_id"] in seen:
            continue
        seen.add(item["connector_id"])
        unique.append(item)
    return unique
