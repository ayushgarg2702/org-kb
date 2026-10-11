"""Request auth context and ACL helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from org_brain.knowledge.models import AccessGrant


@dataclass
class AuthContext:
    organization_id: str
    user_id: str
    profile: str = "repository_read"
    allowed_source_ids: list[str] | None = None  # None = all


PROFILE_CAPS = {
    "metadata_only": {
        "can_read_source": False,
        "can_read_ops": False,
        "can_read_schema": False,
        "can_write": False,
    },
    "repository_read": {
        "can_read_source": True,
        "can_read_ops": False,
        "can_read_schema": False,
        "can_write": False,
    },
    "operational_read": {
        "can_read_source": True,
        "can_read_ops": True,
        "can_read_schema": False,
        "can_write": False,
    },
    "schema_read": {
        "can_read_source": True,
        "can_read_ops": False,
        "can_read_schema": True,
        "can_write": False,
    },
    "action_capable": {
        "can_read_source": True,
        "can_read_ops": True,
        "can_read_schema": True,
        "can_write": True,
    },
}


def resolve_auth_from_headers(headers: dict[str, str]) -> AuthContext:
    mode = os.environ.get("ORG_BRAIN_AUTH_MODE", "dev")
    if mode == "dev":
        org = headers.get("x-org-id") or os.environ.get("ORG_BRAIN_DEV_ORG_ID", "example-org")
        user = headers.get("x-user-id") or os.environ.get("ORG_BRAIN_DEV_USER_ID", "dev-user")
        profile = headers.get("x-profile") or "repository_read"
        return AuthContext(organization_id=org, user_id=user, profile=profile)
    org_header = headers.get("x-org-id")
    user_header = headers.get("x-user-id")
    if not org_header or not user_header:
        raise PermissionError("Missing authentication headers")
    profile = headers.get("x-profile") or "repository_read"
    return AuthContext(organization_id=org_header, user_id=user_header, profile=profile)


def load_grants(session: Session, ctx: AuthContext) -> AuthContext:
    grant = session.scalar(
        select(AccessGrant).where(
            AccessGrant.organization_id == ctx.organization_id,
            AccessGrant.principal.in_([ctx.user_id, "*"]),
        )
    )
    if grant:
        ctx.profile = grant.profile or ctx.profile
        ctx.allowed_source_ids = grant.source_ids or None
    return ctx


def require_cap(ctx: AuthContext, cap: str) -> None:
    caps = PROFILE_CAPS.get(ctx.profile, PROFILE_CAPS["metadata_only"])
    if not caps.get(cap):
        raise PermissionError(f"Profile {ctx.profile} lacks capability {cap}")
