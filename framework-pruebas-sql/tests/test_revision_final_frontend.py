from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_frontend_uses_valid_history_limit_and_safe_error_rendering():
    javascript = Path("frontend/app.js").read_text(encoding="utf-8")

    assert "limit=1000" not in javascript
    assert "limit=100" in javascript
    assert "escapeHTML(e.message)" in javascript
    assert "if (id == 1)" not in javascript

    assert client.get("/api/history/?limit=100").status_code == 200
    assert client.get("/api/history/?limit=101").status_code == 422


def test_final_readme_uses_integrated_ui_and_real_configuration():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "http://127.0.0.1:8000/ui/" in readme
    assert "No abras `frontend/index.html` mediante `file://`" in readme
    assert "ORACLE_TARGET_DSN" not in readme
    assert "CORS_ORIGINS" in readme
