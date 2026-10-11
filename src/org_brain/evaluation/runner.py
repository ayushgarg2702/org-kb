"""Evaluation runner over golden datasets — no fabricated metrics."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session

from org_brain.config.models import OrgConfig
from org_brain.retrieval.engine import QueryEngine


def load_cases(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("cases") or [])


def evaluate_cases(
    session: Session,
    org_id: str,
    config: OrgConfig,
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    engine = QueryEngine(session, org_id, config)
    results = []
    passed = 0
    for case in cases:
        started = time.perf_counter()
        resp = engine.query(case["question"])
        latency_ms = (time.perf_counter() - started) * 1000
        status_ok = resp.status == case.get("expected_status") or (
            case.get("expected_status") == "answered" and resp.status in {"answered", "partial"}
        )
        names = {e["name"] for e in resp.entities}
        expected_names = set(case.get("expected_entity_names") or [])
        overlap = expected_names <= names if expected_names else True
        forbidden = case.get("forbidden_claims") or []
        forbidden_hit = any(f.lower() in resp.answer.lower() for f in forbidden)
        ok = status_ok and overlap and not forbidden_hit
        if case.get("method") == "status_match":
            ok = status_ok and not forbidden_hit
        if ok:
            passed += 1
        results.append(
            {
                "id": case.get("id"),
                "ok": ok,
                "status": resp.status,
                "latency_ms": latency_ms,
                "entity_overlap": sorted(expected_names & names),
                "missing_entities": sorted(expected_names - names),
                "forbidden_hit": forbidden_hit,
            }
        )
    return {
        "total": len(cases),
        "passed": passed,
        "failed": len(cases) - passed,
        "results": results,
        "methodology": "deterministic overlap/status checks; no invented scores",
    }
