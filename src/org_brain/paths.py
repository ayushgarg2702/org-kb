"""Path helpers for master repo assets and org instances."""

from __future__ import annotations

import os
from pathlib import Path


def package_root() -> Path:
    return Path(__file__).resolve().parent


def repo_root() -> Path:
    return package_root().parent.parent


def schemas_dir() -> Path:
    return repo_root() / "schemas"


def templates_dir() -> Path:
    return repo_root() / "templates" / "organization-kb"


def resolve_instance_path(explicit: str | Path | None = None) -> Path:
    raw = explicit or os.environ.get("ORG_BRAIN_INSTANCE")
    if not raw:
        raise ValueError(
            "Organization KB instance path required. Pass --instance or set ORG_BRAIN_INSTANCE."
        )
    return Path(raw).expanduser().resolve()
