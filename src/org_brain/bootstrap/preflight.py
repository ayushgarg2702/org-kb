"""Preflight checks for an org KB instance."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import text

from org_brain.config.loader import ConfigError, load_org_config
from org_brain.knowledge.db import get_engine
from org_brain.parsing.registry import all_parsers


@dataclass
class CheckResult:
    name: str
    status: str  # pass|warn|fail
    message: str
    blocking: bool = True


@dataclass
class PreflightReport:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(c.status == "fail" and c.blocking for c in self.checks)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "checks": [c.__dict__ for c in self.checks],
        }


def run_preflight(instance_dir: Path) -> PreflightReport:
    report = PreflightReport()

    # runtime
    report.checks.append(
        CheckResult("python_runtime", "pass", "Python runtime available", blocking=True)
    )

    # config
    try:
        cfg = load_org_config(instance_dir)
        report.checks.append(CheckResult("config", "pass", f"Loaded org {cfg.organization.id}"))
    except ConfigError as exc:
        report.checks.append(CheckResult("config", "fail", str(exc)))
        return report

    # storage path
    data_dir = (instance_dir / cfg.storage.data_directory).resolve()
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        report.checks.append(CheckResult("data_directory", "pass", str(data_dir)))
    except OSError as exc:
        report.checks.append(CheckResult("data_directory", "fail", str(exc)))

    disk = shutil.disk_usage(str(instance_dir))
    if disk.free < 50 * 1024 * 1024:
        report.checks.append(
            CheckResult("disk_space", "warn", "Less than 50MB free", blocking=False)
        )
    else:
        report.checks.append(CheckResult("disk_space", "pass", f"free={disk.free}"))

    # database
    db_env = cfg.storage.database_url_env
    if not os.environ.get(db_env):
        report.checks.append(
            CheckResult("database", "fail", f"Environment variable {db_env} is not set")
        )
    else:
        try:
            eng = get_engine()
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            report.checks.append(CheckResult("database", "pass", "Database connectivity ok"))
        except Exception as exc:  # noqa: BLE001
            report.checks.append(CheckResult("database", "fail", f"Database error: {exc}"))

    # repos
    for repo in cfg.sources.repositories:
        if not repo.enabled:
            continue
        path = cfg.resolve_repo_path(repo, instance_dir)
        if path.exists():
            report.checks.append(CheckResult(f"repo:{repo.id}", "pass", str(path)))
        else:
            report.checks.append(CheckResult(f"repo:{repo.id}", "fail", f"Missing path {path}"))

    # parsers
    parsers = all_parsers()
    report.checks.append(
        CheckResult(
            "parsers", "pass", f"{len(parsers)} parsers registered: {[p.language for p in parsers]}"
        )
    )

    # model provider optional
    provider = cfg.models.default_provider
    if provider in {"", "none", "configured-provider"}:
        report.checks.append(
            CheckResult(
                "models",
                "warn",
                "No model provider configured — retrieval-only mode",
                blocking=False,
            )
        )
    else:
        report.checks.append(CheckResult("models", "pass", f"provider={provider}", blocking=False))

    # security defaults
    if cfg.security.allow_destructive_actions:
        report.checks.append(
            CheckResult("security", "warn", "Destructive actions enabled", blocking=False)
        )
    else:
        report.checks.append(CheckResult("security", "pass", "Read-only default"))

    return report
