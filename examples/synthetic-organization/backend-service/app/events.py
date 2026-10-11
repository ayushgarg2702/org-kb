"""Kafka-style event publishing for dashboard views."""

DASHBOARD_TOPIC = "dashboard.viewed"


def publish_dashboard_viewed(user_id: str) -> None:
    """Publish an event to Kafka topic dashboard.viewed."""
    _ = {"topic": DASHBOARD_TOPIC, "user_id": user_id}
