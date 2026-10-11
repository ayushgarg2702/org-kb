"""Load and validate organization configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from org_brain.config.models import OrgConfig
from org_brain.paths import schemas_dir


class ConfigError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Missing configuration file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"Configuration must be a mapping: {path}")
    return data


def validate_against_schema(
    data: dict[str, Any], schema_name: str = "organization.schema.json"
) -> None:
    schema_path = schemas_dir() / schema_name
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        msgs = [f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors]
        raise ConfigError("Invalid organization config:\n" + "\n".join(msgs))


def load_org_config(instance_dir: Path) -> OrgConfig:
    path = instance_dir / "org.yaml"
    data = load_yaml(path)
    validate_against_schema(data)
    return OrgConfig.model_validate(data)


def load_policies(instance_dir: Path) -> dict[str, Any]:
    path = instance_dir / "policies.yaml"
    if not path.exists():
        return {}
    return load_yaml(path)
