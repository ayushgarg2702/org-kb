"""Repository file inventory."""

from __future__ import annotations

import fnmatch
import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class InventoredFile:
    path: str
    language: str | None
    content_hash: str
    size_bytes: int
    content: str


_LANG = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".sql": "sql",
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".go": "go",
}


def _match(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, p) or fnmatch.fnmatch(Path(path).name, p) for p in patterns)


def inventory_directory(
    root: Path,
    include: list[str],
    exclude: list[str],
) -> list[InventoredFile]:
    results: list[InventoredFile] = []
    if not root.exists():
        return results
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if _match(rel, exclude) or any(
            part in {"node_modules", ".git", "dist", "build"} for part in path.parts
        ):
            continue
        if include and not _match(rel, include):
            continue
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        digest = hashlib.sha256(raw).hexdigest()
        results.append(
            InventoredFile(
                path=rel,
                language=_LANG.get(path.suffix.lower()),
                content_hash=digest,
                size_bytes=len(raw),
                content=text,
            )
        )
    return results


def revision_for(root: Path) -> str:
    git_head = root / ".git" / "HEAD"
    if git_head.exists():
        content = git_head.read_text(encoding="utf-8").strip()
        if content.startswith("ref:"):
            ref = content.split(" ", 1)[1]
            ref_path = root / ".git" / ref
            if ref_path.exists():
                return ref_path.read_text(encoding="utf-8").strip()[:40]
        return content[:40]
    # content hash of file list
    h = hashlib.sha256()
    for f in sorted(p.as_posix() for p in root.rglob("*") if p.is_file()):
        h.update(f.encode())
    return h.hexdigest()[:40]
