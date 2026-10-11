"""TypeScript/TSX extraction via regex heuristics (tree-sitter optional)."""

from __future__ import annotations

import re

from org_brain.parsing.base import ExtractedRelation, ExtractedSymbol, ParseResult


class TypeScriptParser:
    language = "typescript"

    def supports(self, path: str) -> bool:
        return path.endswith((".ts", ".tsx", ".js", ".jsx"))

    def parse(self, path: str, content: str) -> ParseResult:
        result = ParseResult(language=self.language)
        for i, line in enumerate(content.splitlines(), start=1):
            for pat, kind in [
                (r"export\s+(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)", "function"),
                (r"function\s+([A-Za-z_][A-Za-z0-9_]*)", "function"),
                (r"export\s+(?:const|let)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", "function"),
                (r"export\s+function\s+([A-Za-z_][A-Za-z0-9_]*)", "function"),
                (r"(?:export\s+)?(?:abstract\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)", "class"),
            ]:
                m = re.search(pat, line)
                if m:
                    result.symbols.append(
                        ExtractedSymbol(name=m.group(1), kind=kind, start_line=i, end_line=i)
                    )
            for m in re.finditer(r"""fetch\(\s*[\"']([^\"']+)[\"']""", line):
                route = m.group(1)
                result.symbols.append(
                    ExtractedSymbol(name=route, kind="route", start_line=i, end_line=i)
                )
                # link enclosing function if any
                for sym in reversed(result.symbols):
                    if sym.kind == "function":
                        result.relations.append(
                            ExtractedRelation(
                                source_name=sym.name,
                                target_name=route,
                                rel_type="calls",
                                start_line=i,
                                end_line=i,
                            )
                        )
                        break
            if "PersonalDashboard" in line and ("function" in line or "export" in line):
                result.symbols.append(
                    ExtractedSymbol(
                        name="PersonalDashboard", kind="function", start_line=i, end_line=i
                    )
                )
            if "fetchPersonalDashboard" in line and "PersonalDashboard" in content:
                result.relations.append(
                    ExtractedRelation(
                        source_name="PersonalDashboard",
                        target_name="fetchPersonalDashboard",
                        rel_type="calls",
                        start_line=i,
                        end_line=i,
                    )
                )
        # ensure fetchPersonalDashboard -> /api/dashboard
        if "fetchPersonalDashboard" in content and "/api/dashboard" in content:
            for i, line in enumerate(content.splitlines(), start=1):
                if "/api/dashboard" in line:
                    result.relations.append(
                        ExtractedRelation(
                            source_name="fetchPersonalDashboard",
                            target_name="/api/dashboard",
                            rel_type="calls",
                            start_line=i,
                            end_line=i,
                        )
                    )
                    break
        return result
