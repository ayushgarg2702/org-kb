"""Parser protocol and extract DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ExtractedSymbol:
    name: str
    kind: str  # function|class|route|table|topic|module|import
    start_line: int
    end_line: int
    signature: str | None = None
    attributes: dict = field(default_factory=dict)


@dataclass
class ExtractedRelation:
    source_name: str
    target_name: str
    rel_type: str
    start_line: int
    end_line: int
    attributes: dict = field(default_factory=dict)


@dataclass
class ParseResult:
    language: str
    symbols: list[ExtractedSymbol] = field(default_factory=list)
    relations: list[ExtractedRelation] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    unsupported: bool = False


class Parser(Protocol):
    language: str

    def supports(self, path: str) -> bool: ...

    def parse(self, path: str, content: str) -> ParseResult: ...
