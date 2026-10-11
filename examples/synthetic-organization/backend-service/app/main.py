"""Backend service exposing the personal dashboard API."""

from fastapi import FastAPI

from app.dashboard import get_dashboard_payload

app = FastAPI(title="backend-service")


@app.get("/api/dashboard")
def personal_dashboard() -> dict:
    """HTTP route for the personal dashboard."""
    return get_dashboard_payload()
