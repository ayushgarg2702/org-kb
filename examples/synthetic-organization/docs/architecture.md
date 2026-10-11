# Synthetic org architecture

Personal dashboard UI (`frontend-app`) calls `GET /api/dashboard` on `backend-service`.
Backend reads `user_dashboard` table and publishes `dashboard.viewed`.
`worker-service` consumes `dashboard.viewed`.
