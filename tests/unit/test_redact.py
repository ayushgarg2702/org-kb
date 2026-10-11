from org_brain.security.redact import redact_text


def test_redacts_bearer_and_api_key():
    text = "Authorization: Bearer abcdef123456 api_key=supersecret"
    out = redact_text(text)
    assert "abcdef123456" not in out
    assert "supersecret" not in out
    assert "REDACTED" in out
