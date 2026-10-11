"""Create an organization-owned KB instance from templates."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from org_brain.paths import repo_root, templates_dir


def init_org_instance(
    target: Path,
    org_id: str,
    display_name: str,
    *,
    use_synthetic_sources: bool = True,
) -> Path:
    target = target.expanduser().resolve()
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"Target is not empty: {target}")
    target.mkdir(parents=True, exist_ok=True)

    tmpl = templates_dir()
    for item in tmpl.iterdir():
        dest = target / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

    (target / "var").mkdir(exist_ok=True)
    (target / "extensions").mkdir(exist_ok=True)
    (target / "evaluation" / "results").mkdir(parents=True, exist_ok=True)

    example = repo_root() / "config" / "org.example.yaml"
    org_cfg = yaml.safe_load(example.read_text(encoding="utf-8"))
    org_cfg["organization"]["id"] = org_id
    org_cfg["organization"]["display_name"] = display_name

    if use_synthetic_sources:
        synth = repo_root() / "examples" / "synthetic-organization"
        org_cfg["sources"]["repositories"] = [
            {
                "id": "frontend-app",
                "path": str(synth / "frontend-app"),
                "revision": "HEAD",
                "access_scope": "read-only",
                "enabled": True,
            },
            {
                "id": "backend-service",
                "path": str(synth / "backend-service"),
                "revision": "HEAD",
                "access_scope": "read-only",
                "enabled": True,
            },
            {
                "id": "worker-service",
                "path": str(synth / "worker-service"),
                "revision": "HEAD",
                "access_scope": "read-only",
                "enabled": True,
            },
        ]
        org_cfg["sources"]["documentation"] = {
            "enabled": True,
            "path": str(synth / "docs"),
        }
        org_cfg["sources"]["issue_tracker"] = {
            "enabled": True,
            "path": str(synth / "docs" / "incidents"),
        }

    (target / "org.yaml").write_text(yaml.safe_dump(org_cfg, sort_keys=False), encoding="utf-8")

    policies = repo_root() / "config" / "policies.example.yaml"
    shutil.copy2(policies, target / "policies.yaml")

    connectors = repo_root() / "config" / "connector.example.yaml"
    shutil.copy2(connectors, target / "connectors" / "default.yaml")

    env_example = (
        "ORG_BRAIN_DATABASE_URL=postgresql+psycopg://orgbrain:orgbrain@localhost:5432/orgbrain\n"
        f"ORG_BRAIN_INSTANCE={target}\n"
    )
    (target / ".env.example").write_text(env_example, encoding="utf-8")
    return target
