import os
import sqlite3
import subprocess
import pytest
from sqlalchemy import create_engine, inspect
from fastapi.testclient import TestClient

def get_inspect_info(db_path):
    engine = create_engine(f"sqlite:///{db_path}")
    insp = inspect(engine)
    tables = insp.get_table_names()
    return insp, tables

def test_scenario_a_empty_db(tmp_path):
    db_path = tmp_path / "test_a.db"
    
    # 1. Ejecutar alembic upgrade head en un subproceso
    env = os.environ.copy()
    env["FRAMEWORK_DB_URL"] = f"sqlite:///{db_path}"
    subprocess.run(["alembic", "upgrade", "head"], env=env, check=True)
    
    # 2. Validar esquema completo
    insp, tables = get_inspect_info(db_path)
    assert "suite_test_case" in tables
    assert "suite_test_cases" not in tables
    assert "execution_history" in tables
    
    cols = {col["name"] for col in insp.get_columns("execution_history")}
    assert "duration_ms" in cols
    assert "executed_sql" in cols

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_key_check")
        assert len(cursor.fetchall()) == 0
        
    # 3. Iniciar la API
    os.environ["FRAMEWORK_DB_URL"] = f"sqlite:///{db_path}"
    from app.main import app
    
    # Reload engine
    from app.core import database
    database.engine = create_engine(f"sqlite:///{db_path}")
    database.SessionLocal.configure(bind=database.engine)
    app.dependency_overrides = {}
    
    client = TestClient(app)
    
    # Crear proyecto
    p = client.post("/api/projects/", json={"name": "P1"}).json()
    assert "id" in p
    # Crear conexión
    prof = client.post("/api/connections/", json={
        "project_id": p["id"], "name": "C1", "engine": "ORACLE",
        "host": "localhost", "port": 1521, "service_name": "xe", "username": "u"
    }).json()
    # Crear caso
    case = client.post("/api/test-cases/", json={
        "name": "C1", "sql_query": "SELECT 1", "expected_result": "1", "project_id": p["id"]
    }).json()
    # Crear suite
    suite = client.post("/api/suites/", json={"name": "S1", "project_id": p["id"]}).json()
    # Asociar
    res = client.put(f"/api/suites/{suite['id']}", json={"test_case_ids": [case["id"]]})
    assert res.status_code == 200
    
    # Ejecutar caso
    from unittest.mock import patch, MagicMock
    with patch("app.api.executions.resolve_connection_credentials") as mock_resolve:
        with patch("app.api.executions.TargetDatabaseExecutor") as mock_exec:
            mock_prof = MagicMock()
            mock_prof.id = prof["id"]
            mock_resolve.return_value = ("dsn", "user", "pwd", mock_prof)
            
            mock_instance = mock_exec.return_value
            mock_instance.execute_query.return_value = {
                "success": True, "statement_type": "SELECT", "rows": [{"1": 1}],
                "rowcount": 1, "rollback_applied": False, "rollback_error": None, "error_message": None
            }
            
            res = client.post(f"/api/execute/test-case/{case['id']}", json={"connection_profile_id": prof["id"], "password": "x"})
            assert res.status_code == 200
            
    # Consultar historial
    res = client.get("/api/history/")
    assert res.status_code == 200
    # Fast API sometimes returns list directly, sometimes dict with items
    data = res.json()
    if isinstance(data, list):
        assert len(data) > 0
    else:
        assert len(data["items"]) > 0

def test_scenario_b_legacy(tmp_path):
    db_path = tmp_path / "test_b.db"
    
    # 1. Construir esquema anterior
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE projects (id INTEGER PRIMARY KEY, name TEXT, description TEXT)")
        cursor.execute("INSERT INTO projects (id, name, description) VALUES (1, 'Proyecto general', 'Default')")
        cursor.execute("CREATE TABLE test_cases (id INTEGER PRIMARY KEY, project_id INTEGER, name TEXT, sql_query TEXT, expected_result TEXT)")
        cursor.execute("INSERT INTO test_cases (id, project_id, name, sql_query, expected_result) VALUES (1, 1, 'Old', 'SELECT 1', '1')")
        
        cursor.execute("CREATE TABLE test_suites (id INTEGER PRIMARY KEY, project_id INTEGER, name TEXT, description TEXT)")
        cursor.execute("INSERT INTO test_suites (id, project_id, name, description) VALUES (1, 1, 'Old Suite', 'Old')")
        
        cursor.execute("CREATE TABLE suite_test_cases (suite_id INTEGER, test_case_id INTEGER)")
        cursor.execute("INSERT INTO suite_test_cases (suite_id, test_case_id) VALUES (1, 1)")
        
        cursor.execute("CREATE TABLE execution_history (id INTEGER PRIMARY KEY, project_id INTEGER, test_case_id INTEGER, status TEXT, executed_at TEXT, statement_type TEXT, validation_type TEXT, expected_result TEXT, actual_result TEXT, rowcount INTEGER, rollback_applied BOOLEAN, rollback_error TEXT, error_message TEXT)")
        cursor.execute("INSERT INTO execution_history (project_id, test_case_id, status, executed_at) VALUES (1, 1, 'PASS', '2025')")
        conn.commit()
        
    env = os.environ.copy()
    env["FRAMEWORK_DB_URL"] = f"sqlite:///{db_path}"
    subprocess.run(["alembic", "upgrade", "head"], env=env, check=True)
    
    insp, tables = get_inspect_info(db_path)
    assert "suite_test_case" in tables
    assert "suite_test_cases" not in tables
    cols = {col["name"] for col in insp.get_columns("execution_history")}
    assert "duration_ms" in cols
    assert "executed_sql" in cols
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM suite_test_case")
        assert cursor.fetchone()[0] == 1
        
        cursor.execute("SELECT duration_ms, executed_sql FROM execution_history")
        row = cursor.fetchone()
        assert row[0] == 0.0
        assert row[1] == 'UNKNOWN'
        
        cursor.execute("PRAGMA foreign_key_check")
        assert len(cursor.fetchall()) == 0

def test_scenario_c_no_version(tmp_path):
    db_path = tmp_path / "test_c.db"
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE projects (id INTEGER PRIMARY KEY, name TEXT, description TEXT, created_at TEXT, updated_at TEXT)")
        cursor.execute("INSERT INTO projects (id, name, description) VALUES (1, 'Proyecto general', 'Default')")
        cursor.execute("CREATE TABLE connection_profiles (id INTEGER PRIMARY KEY, project_id INTEGER, name TEXT, engine TEXT, host TEXT, port INTEGER, service_name TEXT, username TEXT, created_at TEXT, updated_at TEXT)")
        cursor.execute("CREATE TABLE test_cases (id INTEGER PRIMARY KEY, project_id INTEGER, name TEXT, sql_query TEXT, validation_type TEXT, expected_result TEXT, created_at TEXT, updated_at TEXT)")
        cursor.execute("INSERT INTO test_cases (id, project_id, name, sql_query, expected_result) VALUES (1, 1, 'Old', 'SELECT 1', '1')")
        cursor.execute("CREATE TABLE test_suites (id INTEGER PRIMARY KEY, project_id INTEGER, name TEXT, description TEXT)")
        cursor.execute("INSERT INTO test_suites (id, project_id, name, description) VALUES (1, 1, 'Old Suite', 'Old')")
        cursor.execute("CREATE TABLE suite_test_cases (suite_id INTEGER, test_case_id INTEGER)")
        cursor.execute("INSERT INTO suite_test_cases (suite_id, test_case_id) VALUES (1, 1)")
        cursor.execute("CREATE TABLE execution_history (id INTEGER PRIMARY KEY, project_id INTEGER, test_case_id INTEGER, suite_id INTEGER, connection_profile_id INTEGER, status TEXT, executed_at TEXT, statement_type TEXT, validation_type TEXT, expected_result TEXT, actual_result TEXT, rowcount INTEGER, rollback_applied BOOLEAN, rollback_error TEXT, error_message TEXT)")
        cursor.execute("INSERT INTO execution_history (project_id, test_case_id, status) VALUES (1, 1, 'PASS')")
        conn.commit()
        
    env = os.environ.copy()
    env["FRAMEWORK_DB_URL"] = f"sqlite:///{db_path}"
    subprocess.run(["alembic", "upgrade", "head"], env=env, check=True)
    
    insp, tables = get_inspect_info(db_path)
    assert "suite_test_case" in tables
    assert "suite_test_cases" not in tables
    cols = {col["name"] for col in insp.get_columns("execution_history")}
    assert "duration_ms" in cols
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_key_check")
        assert len(cursor.fetchall()) == 0
