"""Ingest human-authored memory and incidents from Markdown."""

from __future__ import annotations

from pathlib import Path

from org_brain.knowledge.store import KnowledgeStore
from org_brain.security.redact import redact_text


def ingest_memory_dir(store: KnowledgeStore, root: Path, category: str = "lesson") -> int:
    if not root.exists():
        return 0
    count = 0
    for path in root.rglob("*.md"):
        if path.name.upper() == "README.MD":
            continue
        content = redact_text(path.read_text(encoding="utf-8", errors="replace"))
        lines = content.splitlines()
        summary = lines[0].lstrip("# ").strip() if lines else path.name
        store.add_memory(
            category=category,
            summary=summary[:500],
            content=content,
            entity_names=[],
            source_path=str(path),
            verification_status="human_authored",
        )
        count += 1
    return count
