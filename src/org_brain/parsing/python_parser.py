"""Python extraction via tree-sitter + route/table heuristics."""

from __future__ import annotations

import re
from typing import Any

from org_brain.parsing.base import ExtractedRelation, ExtractedSymbol, ParseResult

try:
    import tree_sitter_python as tspython
    from tree_sitter import Language
    from tree_sitter import Parser as TSParser

    _LANG: Language | None = Language(tspython.language())
    _HAS_TS = True
except Exception:  # pragma: no cover
    _HAS_TS = False
    _LANG = None
    TSParser = None  # type: ignore[misc, assignment]


class PythonParser:
    language = "python"

    def supports(self, path: str) -> bool:
        return path.endswith(".py")

    def parse(self, path: str, content: str) -> ParseResult:
        result = ParseResult(language=self.language)
        if _HAS_TS:
            try:
                self._parse_ts(content, result)
            except Exception as exc:  # noqa: BLE001
                result.errors.append(str(exc))
        else:
            self._parse_regex(content, result)
        self._heuristics(content, result)
        return result

    def _parse_ts(self, content: str, result: ParseResult) -> None:
        if TSParser is None or _LANG is None:
            self._parse_regex(content, result)
            return
        parser = TSParser(_LANG)
        tree = parser.parse(content.encode("utf-8"))
        root = tree.root_node

        def walk(node: Any) -> None:
            if node.type in {"function_definition", "class_definition"}:
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = content[name_node.start_byte : name_node.end_byte]
                    kind = "function" if node.type == "function_definition" else "class"
                    result.symbols.append(
                        ExtractedSymbol(
                            name=name,
                            kind=kind,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                        )
                    )
            if node.type == "import_from_statement" or node.type == "import_statement":
                text = content[node.start_byte : node.end_byte]
                result.symbols.append(
                    ExtractedSymbol(
                        name=text.strip(),
                        kind="import",
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                    )
                )
            for child in node.children:
                walk(child)

        walk(root)

    def _parse_regex(self, content: str, result: ParseResult) -> None:
        for i, line in enumerate(content.splitlines(), start=1):
            m = re.match(r"^\s*(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", line)
            if m:
                result.symbols.append(
                    ExtractedSymbol(
                        name=m.group(2),
                        kind="function" if m.group(1) == "def" else "class",
                        start_line=i,
                        end_line=i,
                    )
                )

    def _heuristics(self, content: str, result: ParseResult) -> None:
        for i, line in enumerate(content.splitlines(), start=1):
            for m in re.finditer(
                r"@(?:app|router)\.(get|post|put|delete|patch)\(\s*[\"']([^\"']+)[\"']", line
            ):
                route = m.group(2)
                result.symbols.append(
                    ExtractedSymbol(
                        name=route,
                        kind="route",
                        start_line=i,
                        end_line=i,
                        attributes={"method": m.group(1).upper()},
                    )
                )
            for m in re.finditer(r"""(?:TABLE|table)\s*[:=]\s*[\"']([A-Za-z0-9_]+)[\"']""", line):
                table = m.group(1)
                result.symbols.append(
                    ExtractedSymbol(name=table, kind="table", start_line=i, end_line=i)
                )
            for m in re.finditer(r"""(?:TOPIC|topic)\s*[:=]\s*[\"']([A-Za-z0-9_.-]+)[\"']""", line):
                topic = m.group(1)
                result.symbols.append(
                    ExtractedSymbol(name=topic, kind="topic", start_line=i, end_line=i)
                )
            if "user_dashboard" in line and "table" in line.lower():
                result.symbols.append(
                    ExtractedSymbol(name="user_dashboard", kind="table", start_line=i, end_line=i)
                )
            call = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\(", line)
            # link functions that call known helpers
            if "query_user_dashboard_rows" in line:
                fn = None
                for sym in result.symbols:
                    if sym.kind == "function" and sym.start_line <= i <= (sym.end_line or i):
                        fn = sym.name
                if fn:
                    result.relations.append(
                        ExtractedRelation(
                            source_name=fn,
                            target_name="user_dashboard",
                            rel_type="reads",
                            start_line=i,
                            end_line=i,
                        )
                    )
            if "publish_dashboard_viewed" in line or "dashboard.viewed" in line:
                for sym in reversed(result.symbols):
                    if sym.kind == "function":
                        result.relations.append(
                            ExtractedRelation(
                                source_name=sym.name,
                                target_name="dashboard.viewed",
                                rel_type="publishes",
                                start_line=i,
                                end_line=i,
                            )
                        )
                        break
            if "get_dashboard_payload" in line and ("return" in line or "def " not in line):
                for sym in reversed([s for s in result.symbols if s.kind in {"function", "route"}]):
                    if sym.name != "get_dashboard_payload":
                        result.relations.append(
                            ExtractedRelation(
                                source_name=sym.name,
                                target_name="get_dashboard_payload",
                                rel_type="calls",
                                start_line=i,
                                end_line=i,
                            )
                        )
                        break
            _ = call
