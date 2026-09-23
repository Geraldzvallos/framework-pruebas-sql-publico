import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
import oracledb
from dotenv import load_dotenv

load_dotenv(".env.oracle")

# Validar que se deban correr las pruebas Oracle
run_oracle = os.getenv("RUN_ORACLE_TESTS", "0") == "1"
test_password = os.getenv("FRAMEWORK_TEST_PASSWORD", "").strip()

pytestmark = pytest.mark.skipif(
    not run_oracle or not test_password,
    reason="Pruebas Oracle desactivadas. Requiere RUN_ORACLE_TESTS=1 y FRAMEWORK_TEST_PASSWORD"
)

ORACLE_HOST = os.getenv("ORACLE_HOST", "127.0.0.1")
ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1521"))
ORACLE_SERVICE = os.getenv("ORACLE_SERVICE", "FREEPDB1")
ORACLE_USER = os.getenv("ORACLE_TEST_USER", "FRAMEWORK_TEST")
ORACLE_PWD = test_password

client = TestClient(app)

def get_real_connection():
    # Helper to check data outside the executor to verify rollback
    return oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PWD,
        dsn=f"{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE}"
    )

@pytest.fixture(autouse=True)
def clean_state():
    # Ensure there is exactly one test row for UPDATE/DELETE tests
    try:
        conn = get_real_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM FRAMEWORK_TEST_ITEMS")
        cursor.execute("INSERT INTO FRAMEWORK_TEST_ITEMS (ID, NAME, ACTIVE) VALUES (1, 'Initial', 1)")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        pytest.fail(f"Fallo al preparar el estado inicial de Oracle: {e}")

@pytest.fixture(scope="module")
def credentials_payload():
    return {
        "dsn": f"{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE}",
        "user": ORACLE_USER,
        "password": ORACLE_PWD
    }

def create_and_execute(test_case_payload, credentials):
    res_create = client.post("/api/test-cases/", json=test_case_payload)
    assert res_create.status_code == 201
    tc_id = res_create.json()["id"]

    res_exec = client.post(f"/api/execute/test-case/{tc_id}", json=credentials)
    assert res_exec.status_code == 200
    return res_exec.json()


@pytest.mark.oracle_integration
def test_escenario_a_select_row_count(credentials_payload):
    """Escenario A — SELECT y ROW_COUNT: PASS"""
    payload = {
        "name": "Test A",
        "sql_query": "SELECT 1 FROM DUAL",
        "validation_type": "ROW_COUNT",
        "expected_result": "1"
    }
    result = create_and_execute(payload, credentials_payload)
    assert result["status"] == "PASS"
    assert result["actual_result"] == "[[1]]"

@pytest.mark.oracle_integration
def test_escenario_b_select_exists(credentials_payload):
    """Escenario B — SELECT y EXISTS: PASS"""
    payload = {
        "name": "Test B",
        "sql_query": "SELECT 1 FROM DUAL",
        "validation_type": "EXISTS",
        "expected_result": "true"
    }
    result = create_and_execute(payload, credentials_payload)
    assert result["status"] == "PASS"

@pytest.mark.oracle_integration
def test_escenario_c_insert_rollback(credentials_payload):
    """Escenario C — INSERT con ROLLBACK: PASS"""
    payload = {
        "name": "Test C",
        "sql_query": "INSERT INTO FRAMEWORK_TEST_ITEMS (ID, NAME, ACTIVE) VALUES (99, 'Test C', 1)",
        "validation_type": "ROW_COUNT",
        "expected_result": "1"
    }
    result = create_and_execute(payload, credentials_payload)
    assert result["status"] == "PASS"
    assert result["rollback_applied"] is True
    
    # Verify rollback worked
    conn = None
    cursor = None
    try:
        conn = get_real_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM FRAMEWORK_TEST_ITEMS WHERE ID = 99")
        count = cursor.fetchone()[0]
        assert count == 0, "El ROLLBACK no se aplico correctamente, el registro existe."
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@pytest.mark.oracle_integration
def test_escenario_d_update_rollback(credentials_payload):
    """Escenario D — UPDATE con ROLLBACK: PASS"""
    payload = {
        "name": "Test D",
        "sql_query": "UPDATE FRAMEWORK_TEST_ITEMS SET NAME = 'Updated' WHERE ID = 1",
        "validation_type": "ROW_COUNT",
        "expected_result": "1"
    }
    result = create_and_execute(payload, credentials_payload)
    assert result["status"] == "PASS"
    assert result["rollback_applied"] is True
    
    # Verify rollback worked
    conn = None
    cursor = None
    try:
        conn = get_real_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT NAME FROM FRAMEWORK_TEST_ITEMS WHERE ID = 1")
        name = cursor.fetchone()[0]
        assert name == "Initial", "El ROLLBACK no se aplico correctamente, el valor fue modificado."
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@pytest.mark.oracle_integration
def test_escenario_e_delete_rollback(credentials_payload):
    """Escenario E — DELETE con ROLLBACK: PASS"""
    payload = {
        "name": "Test E",
        "sql_query": "DELETE FROM FRAMEWORK_TEST_ITEMS WHERE ID = 1",
        "validation_type": "ROW_COUNT",
        "expected_result": "1"
    }
    result = create_and_execute(payload, credentials_payload)
    assert result["status"] == "PASS"
    assert result["rollback_applied"] is True
    
    # Verify rollback worked
    conn = None
    cursor = None
    try:
        conn = get_real_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM FRAMEWORK_TEST_ITEMS WHERE ID = 1")
        count = cursor.fetchone()[0]
        assert count == 1, "El ROLLBACK no se aplico correctamente, el registro fue borrado."
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@pytest.mark.oracle_integration
def test_escenario_f_fail_mismatch(credentials_payload):
    """Escenario F — Diferencia entre esperado y obtenido: FAIL"""
    payload = {
        "name": "Test F",
        "sql_query": "SELECT 1 FROM DUAL",
        "validation_type": "ROW_COUNT",
        "expected_result": "99"
    }
    result = create_and_execute(payload, credentials_payload)
    assert result["status"] == "FAIL"

@pytest.mark.oracle_integration
def test_escenario_g_invalid_sql(credentials_payload):
    """Escenario G — SQL inválido: ERROR"""
    payload = {
        "name": "Test G",
        "sql_query": "SELECT * FROM TABLA_QUE_NO_EXISTE",
        "validation_type": "EXISTS",
        "expected_result": "true"
    }
    result = create_and_execute(payload, credentials_payload)
    assert result["status"] == "ERROR"
    assert "ORA-" in result["error_message"] or "not exist" in result["error_message"]

@pytest.mark.oracle_integration
def test_escenario_h_dangerous_command(credentials_payload):
    """Escenario H — Comando peligroso bloqueado: ERROR"""
    payload = {
        "name": "Test H",
        "sql_query": "DROP TABLE FRAMEWORK_TEST_ITEMS",
        "validation_type": "ROW_COUNT",
        "expected_result": "0"
    }
    result = create_and_execute(payload, credentials_payload)
    assert result["status"] == "ERROR"
    assert "no permitidos" in result["error_message"].lower() or "bloqueada" in result["error_message"].lower() or "ddl" in result["error_message"].lower()
    
    # 5.5 Verify table still exists
    conn = None
    cursor = None
    try:
        conn = get_real_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM FRAMEWORK_TEST_ITEMS")
        count = cursor.fetchone()[0]
        assert count >= 0
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@pytest.mark.oracle_integration
def test_5_1_conexion_correcta(credentials_payload):
    """5.1 Conexión correcta y 5.2 Contraseña incorrecta"""
    # Create project
    proj_res = client.post("/api/projects/", json={"name": "Project 5.1", "description": "Test"})
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    # Create profile
    p_res = client.post("/api/connections/", json={
        "name": "Test Oracle Correct",
        "engine": "ORACLE",
        "host": ORACLE_HOST,
        "port": ORACLE_PORT,
        "service_name": ORACLE_SERVICE,
        "username": ORACLE_USER,
        "project_id": proj_id
    })
    assert p_res.status_code == 201
    conn_id = p_res.json()["id"]

    # Test 5.1 Correct password
    c_res = client.post(f"/api/connections/{conn_id}/test", json={"password": ORACLE_PWD})
    assert c_res.status_code == 200
    assert c_res.json()["success"] is True

    # Test 5.2 Incorrect password
    f_res = client.post(f"/api/connections/{conn_id}/test", json={"password": "WRONG_PASSWORD_123"})
    assert f_res.status_code == 400
    err_msg = f_res.json()["detail"]
    assert "WRONG_PASSWORD_123" not in err_msg
    assert ORACLE_PWD not in err_msg

@pytest.mark.oracle_integration
def test_5_3_historial_real(credentials_payload):
    """5.3 Historial real sin contraseñas"""
    # Create test
    t_res = client.post("/api/test-cases/", json={
        "name": "Test Historial",
        "sql_query": "SELECT 1 FROM DUAL",
        "validation_type": "ROW_COUNT",
        "expected_result": "1"
    })
    tc_id = t_res.json()["id"]

    # Execute
    client.post(f"/api/execute/test-case/{tc_id}", json=credentials_payload)

    # Get history
    h_res = client.get(f"/api/history/?test_case_id={tc_id}")
    assert h_res.status_code == 200
    historial = h_res.json()
    assert len(historial) > 0
    latest = historial[0]
    
    assert latest["status"] in ["PASS", "FAIL", "ERROR"]
    assert "executed_sql" in latest
    assert "expected_result" in latest
    assert "actual_result" in latest
    assert "statement_type" in latest
    assert "rollback_applied" in latest
    assert latest["statement_type"] == "SELECT"
    
    # Assert password is NOT in the history dump
    hist_dump = str(latest)
    assert ORACLE_PWD not in hist_dump

@pytest.mark.oracle_integration
def test_5_4_suite_real(credentials_payload):
    """5.4 Suite real"""
    # Create project
    p_proj = client.post("/api/projects/", json={"name": "Project 5.4", "description": "Test"})
    assert p_proj.status_code == 201
    proj_id = p_proj.json()["id"]

    # Create profile
    p_conn = client.post("/api/connections/", json={
        "name": "Test Oracle Suite",
        "engine": "ORACLE",
        "host": ORACLE_HOST,
        "port": ORACLE_PORT,
        "service_name": ORACLE_SERVICE,
        "username": ORACLE_USER,
        "project_id": proj_id
    })
    assert p_conn.status_code == 201
    conn_id = p_conn.json()["id"]

    # Create suite
    s_res = client.post("/api/suites/", json={
        "name": "Suite Real Oracle",
        "project_id": proj_id
    })
    assert s_res.status_code == 201
    suite_id = s_res.json()["id"]

    # Create cases
    t_res = client.post("/api/test-cases/", json={
        "name": "TC Suite",
        "sql_query": "SELECT 1 FROM DUAL",
        "validation_type": "ROW_COUNT",
        "expected_result": "1"
    })
    assert t_res.status_code == 201
    tc_id = t_res.json()["id"]

    # Assign case to suite
    client.post(f"/api/suites/{suite_id}/test-cases/{tc_id}")

    # Execute Suite
    e_res = client.post(f"/api/execute/suite/{suite_id}", json={
        "connection_profile_id": conn_id,
        "password": ORACLE_PWD
    })
    assert e_res.status_code == 200
    summary = e_res.json()
    
    assert summary["total_tests"] >= 1
    assert summary["passed"] >= 1
    assert "failed" in summary
    assert "errors" in summary
    assert "details" in summary

    # Verify history of the suite
    sh_res = client.get(f"/api/history/?suite_id={suite_id}")
    assert sh_res.status_code == 200
    suite_historial = sh_res.json()
    assert len(suite_historial) > 0
    assert suite_historial[0]["suite_id"] == suite_id
