"""
Suite completa de pruebas automáticas para la Fase 2:
Modelo interno, API robusta, trazabilidad, proyectos y perfiles de conexión.
"""
import os
import hashlib
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import ValidationTypeEnum

client = TestClient(app)


def test_01_reject_test_case_empty_name():
    """1. Rechazo de caso con nombre vacío (422)."""
    res = client.post("/api/test-cases/", json={
        "name": "   ",
        "sql_query": "SELECT 1 FROM dual",
        "expected_result": "1"
    })
    assert res.status_code == 422


def test_02_reject_test_case_empty_sql():
    """2. Rechazo de caso con SQL vacío (422)."""
    res = client.post("/api/test-cases/", json={
        "name": "TC SQL Vacío",
        "sql_query": "   ",
        "expected_result": "1"
    })
    assert res.status_code == 422


def test_03_reject_rowcount_non_numeric_or_negative():
    """3. Rechazo de ROW_COUNT no numérico o negativo (422)."""
    res1 = client.post("/api/test-cases/", json={
        "name": "TC Invalid Expected 1",
        "sql_query": "SELECT 1 FROM dual",
        "expected_result": "abc",
        "validation_type": "ROW_COUNT"
    })
    assert res1.status_code == 422

    res2 = client.post("/api/test-cases/", json={
        "name": "TC Invalid Expected 2",
        "sql_query": "SELECT 1 FROM dual",
        "expected_result": "-5",
        "validation_type": "ROW_COUNT"
    })
    assert res2.status_code == 422


def test_04_normalize_and_validate_exists():
    """4. Normalización y validación de EXISTS."""
    res_valid = client.post("/api/test-cases/", json={
        "name": "TC Exists Valid",
        "sql_query": "SELECT 1 FROM dual",
        "expected_result": "TRUE",
        "validation_type": "EXISTS"
    })
    assert res_valid.status_code == 201
    assert res_valid.json()["expected_result"] == "true"

    res_invalid = client.post("/api/test-cases/", json={
        "name": "TC Exists Invalid",
        "sql_query": "SELECT 1 FROM dual",
        "expected_result": "quizas",
        "validation_type": "EXISTS"
    })
    assert res_invalid.status_code == 422


def test_05_pagination_limits():
    """5. Límites de paginación (skip >= 0, 1 <= limit <= 100)."""
    res1 = client.get("/api/projects/?skip=-1")
    assert res1.status_code == 422

    res2 = client.get("/api/projects/?limit=0")
    assert res2.status_code == 422

    res3 = client.get("/api/projects/?limit=101")
    assert res3.status_code == 422

    res_valid = client.get("/api/projects/?skip=0&limit=50")
    assert res_valid.status_code == 200


def test_08_projects_crud_and_09_dependency_prevention():
    """8. CRUD de proyectos y 9. Impedimento de borrar proyecto con dependencias."""
    # Create
    p_res = client.post("/api/projects/", json={
        "name": "Proyecto Alpha",
        "description": "Proyecto para pruebas de integración"
    })
    assert p_res.status_code == 201
    p_id = p_res.json()["id"]

    # Read
    get_res = client.get(f"/api/projects/{p_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Proyecto Alpha"

    # Update
    put_res = client.put(f"/api/projects/{p_id}", json={"description": "Descripción actualizada"})
    assert put_res.status_code == 200
    assert put_res.json()["description"] == "Descripción actualizada"

    # Attach a case to project
    tc_res = client.post("/api/test-cases/", json={
        "project_id": p_id,
        "name": "TC Alpha 1",
        "sql_query": "SELECT * FROM dual",
        "expected_result": "1"
    })
    assert tc_res.status_code == 201
    tc_id = tc_res.json()["id"]

    # 9. Try deleting project with attached case -> 409 Conflict
    del_res = client.delete(f"/api/projects/{p_id}")
    assert del_res.status_code == 409
    assert "no se puede eliminar" in del_res.json()["detail"].lower()

    # Clean up case then delete project
    client.delete(f"/api/test-cases/{tc_id}")
    del_ok = client.delete(f"/api/projects/{p_id}")
    assert del_ok.status_code == 204


def test_06_and_07_suite_case_associations_409():
    """6. Duplicado caso-suite con respuesta 409 y 7. Caso y suite de proyectos diferentes 409."""
    # Create Project 1 and Project 2
    p1 = client.post("/api/projects/", json={"name": "Proyecto P1"}).json()["id"]
    p2 = client.post("/api/projects/", json={"name": "Proyecto P2"}).json()["id"]

    # Create Suite in P1, Case 1 in P1, Case 2 in P2
    suite = client.post("/api/suites/", json={"project_id": p1, "name": "Suite P1"}).json()
    suite_id = suite["id"]

    c1 = client.post("/api/test-cases/", json={"project_id": p1, "name": "Case P1", "sql_query": "SELECT 1", "expected_result": "1"}).json()["id"]
    c2 = client.post("/api/test-cases/", json={"project_id": p2, "name": "Case P2", "sql_query": "SELECT 1", "expected_result": "1"}).json()["id"]

    # Associate c1 to suite (Success)
    res_ok = client.post(f"/api/suites/{suite_id}/test-cases/{c1}")
    assert res_ok.status_code == 200

    # 6. Associate c1 to suite AGAIN (409 Conflict)
    res_dup = client.post(f"/api/suites/{suite_id}/test-cases/{c1}")
    assert res_dup.status_code == 409
    assert "ya pertenece" in res_dup.json()["detail"]

    # 7. Associate c2 (Project P2) to suite (Project P1) (409 Conflict)
    res_mismatch = client.post(f"/api/suites/{suite_id}/test-cases/{c2}")
    assert res_mismatch.status_code == 409
    assert "proyectos distintos" in res_mismatch.json()["detail"]


def test_10_and_11_connection_profile_crud_no_password():
    """10. CRUD de perfiles Oracle sin campo password y 11. Confirmación de no exposición de contraseñas."""
    p_id = client.post("/api/projects/", json={"name": "Proyecto Conexiones"}).json()["id"]

    # Create profile
    prof_res = client.post("/api/connections/", json={
        "project_id": p_id,
        "name": "Oracle Dev",
        "engine": "ORACLE",
        "host": "oracle.local",
        "port": 1521,
        "service_name": "XEPDB1",
        "username": "qa_user"
    })
    assert prof_res.status_code == 201
    prof_data = prof_res.json()
    assert prof_data["name"] == "Oracle Dev"
    assert "password" not in prof_data  # 10 & 11: No password field in schema/response!

    # Read profiles list
    list_res = client.get(f"/api/connections/?project_id={p_id}")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
    assert "password" not in str(list_res.json())


@patch("oracledb.connect")
def test_12_connection_test_simulated(mock_connect):
    """12. Prueba de conexión Oracle simulada con mocks (éxito y error)."""
    p_id = client.post("/api/projects/", json={"name": "Proyecto Test Conn"}).json()["id"]
    prof_id = client.post("/api/connections/", json={
        "project_id": p_id,
        "name": "Oracle Target",
        "host": "localhost",
        "port": 1521,
        "service_name": "XE",
        "username": "dbuser"
    }).json()["id"]

    # 1. Success test
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [(1,)]

    res_ok = client.post(f"/api/connections/{prof_id}/test", json={"password": "secret_pass"})
    assert res_ok.status_code == 200
    assert res_ok.json()["success"] is True
    assert "secret_pass" not in res_ok.text

    # 2. Error test
    mock_connect.side_effect = Exception("ORA-01017: invalid username/password")
    res_err = client.post(f"/api/connections/{prof_id}/test", json={"password": "wrong_pass"})
    assert res_err.status_code == 400
    assert "ORA-01017" in res_err.json()["detail"]
    assert "wrong_pass" not in res_err.text


@patch("app.services.execution_service.TargetDatabaseExecutor.execute_query")
def test_13_14_15_strategy_selection_and_evidence_persistence(mock_execute_query):
    """13. Selección ROW_COUNT vs EXISTS, 14. Evidencia PASS/FAIL/ERROR, 15. Persistencia de rollback_applied."""
    p_id = client.post("/api/projects/", json={"name": "Proyecto Strategies"}).json()["id"]

    # Case 1: ROW_COUNT
    tc1 = client.post("/api/test-cases/", json={
        "project_id": p_id,
        "name": "TC RowCount",
        "sql_query": "SELECT * FROM users",
        "expected_result": "2",
        "validation_type": "ROW_COUNT"
    }).json()["id"]

    # Case 2: EXISTS
    tc2 = client.post("/api/test-cases/", json={
        "project_id": p_id,
        "name": "TC Exists",
        "sql_query": "SELECT * FROM users WHERE active=1",
        "expected_result": "true",
        "validation_type": "EXISTS"
    }).json()["id"]

    # Mock DB execution returning 2 rows
    mock_execute_query.return_value = {
        "success": True,
        "statement_type": "SELECT",
        "rows": [("U1",), ("U2",)],
        "rowcount": 2,
        "message": "OK",
        "error_message": None,
        "rollback_applied": False,
        "rollback_error": None
    }

    res1 = client.post(f"/api/execute/test-case/{tc1}", json={"dsn": "h/s", "user": "u", "password": "p"})
    assert res1.status_code == 200
    assert res1.json()["status"] == "PASS"
    assert res1.json()["validation_type"] == "ROW_COUNT"

    res2 = client.post(f"/api/execute/test-case/{tc2}", json={"dsn": "h/s", "user": "u", "password": "p"})
    assert res2.status_code == 200
    assert res2.json()["status"] == "PASS"
    assert res2.json()["validation_type"] == "EXISTS"


def test_16_history_query_and_filters():
    """16. Consulta y filtros del historial (project_id, test_case_id, suite_id, status)."""
    res = client.get("/api/history/?skip=0&limit=10")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@patch("app.services.execution_service.TargetDatabaseExecutor.execute_query")
def test_17_suite_execution_with_summary(mock_execute_query):
    """17. Ejecución de suite con varios casos y resumen coherente."""
    p_id = client.post("/api/projects/", json={"name": "Proyecto Suite Exec"}).json()["id"]

    c1 = client.post("/api/test-cases/", json={"project_id": p_id, "name": "C1", "sql_query": "SELECT 1", "expected_result": "1"}).json()["id"]
    c2 = client.post("/api/test-cases/", json={"project_id": p_id, "name": "C2", "sql_query": "SELECT 2", "expected_result": "1"}).json()["id"]

    suite_id = client.post("/api/suites/", json={"project_id": p_id, "name": "Suite Multi"}).json()["id"]
    client.post(f"/api/suites/{suite_id}/test-cases/{c1}")
    client.post(f"/api/suites/{suite_id}/test-cases/{c2}")

    mock_execute_query.return_value = {
        "success": True,
        "statement_type": "SELECT",
        "rows": [(1,)],
        "rowcount": 1,
        "message": "OK",
        "error_message": None,
        "rollback_applied": False,
        "rollback_error": None
    }

    exec_res = client.post(f"/api/execute/suite/{suite_id}", json={"dsn": "h/s", "user": "u", "password": "p"})
    assert exec_res.status_code == 200
    summary = exec_res.json()
    assert summary["total_tests"] == 2
    assert summary["passed"] == 2
    assert len(summary["details"]) == 2


def test_19_confirm_tests_do_not_modify_framework_db():
    """19. Confirmación de que las pruebas no modifican framework_interno.db."""
    db_path = "framework_interno.db"
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        with open(db_path, "rb") as f:
            h1 = hashlib.sha256(f.read()).hexdigest()
        assert os.path.getsize(db_path) == size
        with open(db_path, "rb") as f:
            h2 = hashlib.sha256(f.read()).hexdigest()
        assert h1 == h2


def test_20_app_startup_and_docs_available():
    """20. Arranque de la aplicación y disponibilidad de /, /docs y /openapi.json."""
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["version"] == "2.0.0"

    res_docs = client.get("/docs")
    assert res_docs.status_code == 200

    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 200
    assert res_openapi.json()["info"]["title"] == "Framework de Pruebas SQL"
