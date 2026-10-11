CREATE TABLE user_dashboard (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    widget_key TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_dashboard_user ON user_dashboard (user_id);
