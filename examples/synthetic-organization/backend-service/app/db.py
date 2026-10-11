"""Database access for dashboard data."""

# Table: user_dashboard
DASHBOARD_TABLE = "user_dashboard"


def query_user_dashboard_rows(user_id: str) -> list[dict]:
    """SELECT widget data FROM user_dashboard WHERE user_id = ?"""
    # Synthetic stub — real orgs would use a DB driver.
    return [{"id": "w1", "title": "Continue listening", "user_id": user_id}]
