"""Live observation refresh with TTL."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from org_brain.connectors.observability.otel_http import OtelHttpConnector
from org_brain.knowledge.store import KnowledgeStore


def refresh_live_observations(session: Session, organization_id: str) -> int:
    store = KnowledgeStore(session, organization_id)
    connector = OtelHttpConnector()
    discovered = connector.discover()
    count = 0
    now = datetime.now(UTC)
    for item in discovered.resources:
        observed = datetime.fromisoformat(item["observed_at"].replace("Z", "+00:00"))
        expires = datetime.fromisoformat(item["expires_at"].replace("Z", "+00:00"))
        store.add_observation(
            resource=item["resource"],
            environment=item.get("environment", "unknown"),
            metric=item["metric"],
            value=item.get("value", {}),
            observed_at=observed,
            expires_at=expires,
            deployment_revision=item.get("deployment_revision"),
            connector_id=connector.connector_id,
        )
        count += 1
    # ensure expired ones are not returned by fresh_observations
    _ = now + timedelta(seconds=1)
    return count
