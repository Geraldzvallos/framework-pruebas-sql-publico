import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
import base64

@pytest.fixture(autouse=True)
def setup_auth_env(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_ENABLED", "true")
    monkeypatch.setenv("APP_ACCESS_USERNAME", "admin")
    monkeypatch.setenv("APP_ACCESS_PASSWORD", "secret")

def test_auth_disabled(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_ENABLED", "false")
    client = TestClient(app)
    response = client.get("/api/projects/")
    # Asumimos que projects está vacío, por lo que retorna 200 []
    assert response.status_code == 200
    
def test_auth_enabled_no_credentials():
    client = TestClient(app)
    endpoints = ["/ui/", "/api/projects/", "/docs", "/openapi.json"]
    for ep in endpoints:
        response = client.get(ep)
        assert response.status_code == 401

def test_auth_enabled_valid_credentials():
    client = TestClient(app)
    auth = base64.b64encode(b"admin:secret").decode("utf-8")
    headers = {"Authorization": f"Basic {auth}"}
    
    # /api/projects/
    response = client.get("/api/projects/", headers=headers)
    assert response.status_code == 200
    
    # /docs
    response = client.get("/docs", headers=headers)
    assert response.status_code == 200

def test_auth_enabled_invalid_credentials():
    client = TestClient(app)
    auth = base64.b64encode(b"admin:wrong").decode("utf-8")
    headers = {"Authorization": f"Basic {auth}"}
    
    response = client.get("/api/projects/", headers=headers)
    assert response.status_code == 401

def test_healthcheck_always_available():
    client = TestClient(app)
    # Sin credenciales
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "El motor del Framework SQL está en línea.", "version": "2.0.0"}
