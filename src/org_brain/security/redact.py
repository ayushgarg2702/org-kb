"""Secret redaction helpers."""

from __future__ import annotations

import re

_PATTERNS = [
    (
        re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"]?([^\s'\"]+)"),
        lambda m: f"{m.group(1)}=***REDACTED***",
    ),
    (
        re.compile(r"(?i)(authorization)\s*[:=]\s*Bearer\s+\S+"),
        lambda m: f"{m.group(1)}: Bearer ***REDACTED***",
    ),
    (
        re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*"),
        lambda m: "Bearer ***REDACTED***",
    ),
]


def redact_text(text: str) -> str:
    redacted = text
    for pat, repl in _PATTERNS:
        redacted = pat.sub(repl, redacted)
    return redacted
