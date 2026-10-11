# INC-001: Personal dashboard slow after release

## Symptom

Personal dashboard p95 latency rose after deploy of backend-service.

## Root cause evidence

Slow `SELECT` on `user_dashboard` missing index usage in staging (historical). Index added in migration `001_user_dashboard.sql`.

## Fix

Ensure `idx_user_dashboard_user` is present. Verified in staging.

## Status

Resolved — lesson recorded for future agents.
