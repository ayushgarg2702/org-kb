"""Dashboard domain logic and database access."""

from app.db import query_user_dashboard_rows
from app.events import publish_dashboard_viewed


def get_dashboard_payload(user_id: str = "demo-user") -> dict:
    """Load dashboard rows from the user_dashboard table and emit an event."""
    rows = query_user_dashboard_rows(user_id)
    publish_dashboard_viewed(user_id)
    return {"user_id": user_id, "widgets": rows}
