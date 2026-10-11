"""Parser registry."""

from __future__ import annotations

from org_brain.parsing.base import Parser, ParseResult
from org_brain.parsing.markdown_parser import MarkdownParser
from org_brain.parsing.python_parser import PythonParser
from org_brain.parsing.sql_parser import SqlParser
from org_brain.parsing.typescript_parser import TypeScriptParser


def all_parsers() -> list[Parser]:
    return [PythonParser(), TypeScriptParser(), SqlParser(), MarkdownParser()]


def parse_file(path: str, content: str) -> ParseResult:
    for parser in all_parsers():
        if parser.supports(path):
            return parser.parse(path, content)
    return ParseResult(language="unknown", unsupported=True, errors=["no parser"])
