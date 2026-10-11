"""Markdown / memory document extraction."""

from __future__ import annotations

import re

from org_brain.parsing.base import ExtractedSymbol, ParseResult


class MarkdownParser:
    language = "markdown"

    def supports(self, path: str) -> bool:
        return path.endswith((".md", ".markdown"))

    def parse(self, path: str, content: str) -> ParseResult:
        result = ParseResult(language=self.language)
        title = None
        for i, line in enumerate(content.splitlines(), start=1):
            m = re.match(r"^#\s+(.+)$", line)
            if m and title is None:
                title = m.group(1).strip()
                result.symbols.append(
                    ExtractedSymbol(name=title, kind="document", start_line=i, end_line=i)
                )
            for token in re.findall(r"`([^`]+)`", line):
                if "/" in token or "." in token or token.isidentifier():
                    result.symbols.append(
                        ExtractedSymbol(
                            name=token,
                            kind="reference",
                            start_line=i,
                            end_line=i,
                            attributes={"from_doc": True},
                        )
                    )
        return result
