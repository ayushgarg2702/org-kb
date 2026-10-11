from pathlib import Path

from org_brain.config.loader import load_org_config
from org_brain.paths import repo_root


def test_example_org_config_validates(tmp_path: Path):
    # copy example into temp instance
    example = (repo_root() / "config" / "org.example.yaml").read_text(encoding="utf-8")
    (tmp_path / "org.yaml").write_text(example, encoding="utf-8")
    cfg = load_org_config(tmp_path)
    assert cfg.organization.id == "example-org"
    assert cfg.api_version == "org-brain/v1"
