from org_brain.connectors.mcp.adapter import McpGenericConnector
from org_brain.connectors.registry import list_connector_descriptors


def test_connector_registry_lists_builtins():
    ids = {c["connector_id"] for c in list_connector_descriptors()}
    assert "git.local" in ids
    assert "mcp.generic" in ids
    assert "otel.http" in ids


def test_mcp_allowlist_enforced():
    import pytest

    mcp = McpGenericConnector(allowlist_tools=["safe_tool"])
    with pytest.raises(PermissionError):
        mcp.fetch("evil_tool")
