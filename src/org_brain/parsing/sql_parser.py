"""SQL DDL extraction."""

from __future__ import annotations

import re

from org_brain.parsing.base import ExtractedSymbol, ParseResult


class SqlParser:
    language = "sql"

    def supports(self, path: str) -> bool:
        return path.endswith(".sql")

    def parse(self, path: str, content: str) -> ParseResult:
        result = ParseResult(language=self.language)
        for i, line in enumerate(content.splitlines(), start=1):
            m = re.search(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z0-9_]+)", line, re.I)
            if m:
                result.symbols.append(
                    ExtractedSymbol(name=m.group(1), kind="table", start_line=i, end_line=i)
                )
            m = re.search(r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+([A-Za-z0-9_]+)", line, re.I)
            if m:
                result.symbols.append(
                    ExtractedSymbol(name=m.group(1), kind="index", start_line=i, end_line=i)
                )
        return result
