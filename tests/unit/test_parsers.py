from org_brain.parsing.registry import parse_file


def test_python_extracts_route_and_function():
    content = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/api/dashboard")
def personal_dashboard():
    return {}
"""
    result = parse_file("app/main.py", content)
    names = {s.name for s in result.symbols}
    assert "personal_dashboard" in names
    assert "/api/dashboard" in names


def test_typescript_extracts_fetch_route():
    content = """
export async function fetchPersonalDashboard() {
  return fetch("/api/dashboard");
}
"""
    result = parse_file("src/api/dashboardClient.ts", content)
    assert any(s.name == "fetchPersonalDashboard" for s in result.symbols)
    assert any(r.target_name == "/api/dashboard" for r in result.relations)


def test_sql_extracts_table():
    content = "CREATE TABLE user_dashboard (id SERIAL PRIMARY KEY);"
    result = parse_file("migrations/001.sql", content)
    assert any(s.name == "user_dashboard" and s.kind == "table" for s in result.symbols)


def test_unsupported_extension():
    result = parse_file("binary.bin", "\x00\x01")
    assert result.unsupported
