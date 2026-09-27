import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint_available():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_docs_endpoints_available():
    response_docs = client.get("/docs")
    assert response_docs.status_code == 200

    response_openapi = client.get("/openapi.json")
    assert response_openapi.status_code == 200

def test_ui_endpoint_available():
    # El frontend debe estar servido en /ui/
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SQL QA Framework" in response.text

def test_ui_assets_available():
    # Verificar que app.js carga correctamente
    response = client.get("/ui/app.js")
    assert response.status_code == 200
    assert "application/javascript" in response.headers["content-type"] or "text/javascript" in response.headers["content-type"]
    assert "fetchAPI" in response.text

def test_api_integration_contracts():
    # Validar que los endpoints requeridos por el frontend siguen respondiendo
    res_proj = client.get("/api/projects/")
    assert res_proj.status_code == 200
    
    res_conn = client.get("/api/connections/")
    assert res_conn.status_code == 200
    
    res_cases = client.get("/api/test-cases/")
    assert res_cases.status_code == 200
    
    res_suites = client.get("/api/suites/")
    assert res_suites.status_code == 200
    
    res_hist = client.get("/api/history/")
    assert res_hist.status_code == 200

def test_no_passwords_in_connection_list():
    # Asegurar que el contrato de seguridad se mantiene: no devolver contraseñas
    res = client.get("/api/connections/")
    assert res.status_code == 200
    for conn in res.json():
        assert "password" not in conn
