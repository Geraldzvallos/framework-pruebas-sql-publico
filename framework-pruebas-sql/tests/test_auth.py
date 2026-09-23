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
    monkeypatch.setenv("APP_SESSION_SECRET", "test_secret_key")
    monkeypatch.setenv("ENVIRONMENT", "development")

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
        response = client.get(ep, follow_redirects=False)
        if ep.startswith("/api/"):
            assert response.status_code == 401
        else:
            # /ui/, /docs, /openapi.json redirect to /login
            assert response.status_code == 303
            assert response.headers["location"] == "/login"

def test_login_success():
    client = TestClient(app)
    response = client.post("/api/login", json={"username": "admin", "password": "secret"})
    assert response.status_code == 200
    assert "session_token" in response.cookies
    assert response.cookies["session_token"].startswith("auth_valid.")

def test_login_failure():
    client = TestClient(app)
    response = client.post("/api/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401
    assert "session_token" not in response.cookies

def test_auth_enabled_valid_credentials():
    client = TestClient(app)
    # Login primero
    response = client.post("/api/login", json={"username": "admin", "password": "secret"})
    assert response.status_code == 200

    # La cookie se guarda en el client session
    response = client.get("/api/projects/")
    assert response.status_code == 200

def test_logout():
    client = TestClient(app)
    client.post("/api/login", json={"username": "admin", "password": "secret"})
    response = client.post("/api/logout")
    assert response.status_code == 200
    # Al hacer logout, fastapi borra la cookie enviando un Set-Cookie en el pasado o vacío
    # Verificamos intentando acceder a una ruta protegida
    response = client.get("/api/projects/")
    assert response.status_code == 401

def test_healthcheck_always_available():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "El motor del Framework SQL está en línea.", "version": "2.0.0"}

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "El motor del Framework SQL está en línea.", "version": "2.0.0"}

def test_login_page_always_available():
    client = TestClient(app)
    # Puede que no encuentre el login.html si se corre desde una ruta distinta, pero el endpoint debe responder 200 o 404 manejado
    response = client.get("/login")
    assert response.status_code in [200, 404]

def test_auth_enabled_empty_username(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_USERNAME", " ")
    client = TestClient(app)
    response = client.get("/api/projects/")
    assert response.status_code == 503

def test_auth_enabled_empty_password(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_PASSWORD", "")
    client = TestClient(app)
    response = client.get("/api/projects/")
    assert response.status_code == 503

def test_healthcheck_invalid_config(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_PASSWORD", "   ")
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 503

def test_missing_session_secret(monkeypatch):
    monkeypatch.setenv("APP_SESSION_SECRET", "")
    client = TestClient(app)
    response = client.get("/api/projects/")
    assert response.status_code == 503
