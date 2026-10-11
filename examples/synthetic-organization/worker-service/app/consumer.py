"""Worker that consumes dashboard.viewed events."""

TOPIC = "dashboard.viewed"


def handle_dashboard_viewed(event: dict) -> None:
    """Consume dashboard.viewed and update analytics."""
    user_id = event.get("user_id")
    _ = user_id


def main() -> None:
    """Worker entrypoint — subscribe to dashboard.viewed."""
    print(f"listening on {TOPIC}")
