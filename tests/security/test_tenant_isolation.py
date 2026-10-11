import pytest

from org_brain.auth.context import PROFILE_CAPS, AuthContext, require_cap


def test_metadata_only_cannot_read_source():
    ctx = AuthContext(organization_id="a", user_id="u", profile="metadata_only")
    with pytest.raises(PermissionError):
        require_cap(ctx, "can_read_source")


def test_action_capable_has_write():
    assert PROFILE_CAPS["action_capable"]["can_write"] is True
    assert PROFILE_CAPS["repository_read"]["can_write"] is False
