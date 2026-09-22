"""
Pruebas de integración de la API utilizando FastAPI TestClient y base de datos aislada.
"""
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_delete_non_existent_test_case_returns_404():
    """Verifica que eliminar un ID inexistente devuelva HTTP 404."""
    response = client.delete("/api/test-cases/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Caso de prueba no encontrado."


def test_execute_raw_controlled_error_returns_400():
    """Verifica que errores SQL controlados (ej. DDL prohibido) devuelvan HTTP 400."""
    payload = {
        "dsn": "localhost/xe",
        "user": "test_user",
        "password": "super_secret_password_999",
        "sql_query": "DROP TABLE users"
    }
    response = client.post("/api/execute/raw", json=payload)
    assert response.status_code == 400
    assert "Rechazado por seguridad" in response.json()["detail"]
    assert "super_secret_password_999" not in response.text  # Sin fugas de contraseñas


@patch("app.api.executions.TargetDatabaseExecutor.execute_query")
def test_execute_saved_test_case_and_suite_without_exposing_passwords(mock_execute_query):
    """Punto 4.16: Ejecución individual y por suite sin requerir sql_query ni exponer contraseñas."""
    mock_execute_query.return_value = {
        "success": True,
        "statement_type": "SELECT",
        "rows": [("Val1",)],
        "rowcount": 1,
        "message": "OK",
        "error_message": None,
        "rollback_applied": False,
        "rollback_error": None
    }

    # 1. Crear un caso de prueba
    tc_res = client.post("/api/test-cases/", json={
        "name": "TC Secret Test",
        "description": "TestCase de Integración",
        "sql_query": "SELECT * FROM dual",
        "expected_result": "1"
    })
    assert tc_res.status_code == 201
    tc_id = tc_res.json()["id"]

    # 2. Ejecutar el caso guardado pasando sólo credenciales (SIN sql_query en el body)
    secret_pass = "my_top_secret_oracle_pass_777"
    exec_res = client.post(f"/api/execute/test-case/{tc_id}", json={
        "dsn": "localhost/xe",
        "user": "oracle_user",
        "password": secret_pass
    })
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["status"] == "PASS"
    assert secret_pass not in str(exec_data)

    # 3. Crear una Suite y vincularle el caso
    suite_res = client.post("/api/suites/", json={
        "name": "Suite Secreta",
        "description": "Prueba de Suite"
    })
    assert suite_res.status_code == 201
    suite_id = suite_res.json()["id"]


    add_res = client.post(f"/api/suites/{suite_id}/test-cases/{tc_id}")
    assert add_res.status_code == 200

    # 4. Ejecutar la suite completa pasando sólo credenciales (SIN sql_query en el body)
    exec_suite_res = client.post(f"/api/execute/suite/{suite_id}", json={
        "dsn": "localhost/xe",
        "user": "oracle_user",
        "password": secret_pass
    })
    assert exec_suite_res.status_code == 200
    suite_summary = exec_suite_res.json()
    assert suite_summary["passed"] == 1
    assert secret_pass not in str(suite_summary)


def test_list_cases_and_suites_functional():
    """Verifica el correcto funcionamiento de los endpoints de listado de casos y suites."""
    tc_res = client.get("/api/test-cases/")
    assert tc_res.status_code == 200
    assert isinstance(tc_res.json(), list)

    suites_res = client.get("/api/suites/")
    assert suites_res.status_code == 200
    assert isinstance(suites_res.json(), list)
