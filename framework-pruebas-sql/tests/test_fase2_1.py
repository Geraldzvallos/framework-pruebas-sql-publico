import os
import sqlite3
import subprocess
import tempfile
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_alembic(db_path, cmd):
    env = os.environ.copy()
    env["FRAMEWORK_DB_URL"] = f"sqlite:///{db_path}"
    # Run alembic
    res = subprocess.run(["alembic"] + cmd, env=env, capture_output=True, text=True)
    return res

def test_migration_empty_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        res = run_alembic(db_path, ["upgrade", "head"])
        assert res.returncode == 0
        
        # Check if tables exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        assert "projects" in tables
        assert "connection_profiles" in tables
        assert "test_cases" in tables
        assert "alembic_version" in tables
        
        # Check foreign_key_check
        cursor.execute("PRAGMA foreign_key_check")
        fk_issues = cursor.fetchall()
        assert len(fk_issues) == 0
        
        # Check alembic_version
        cursor.execute("SELECT version_num FROM alembic_version")
        version = cursor.fetchone()[0]
        assert version == "002"
        
        cursor.close()
        conn.close()
    finally:
        try:
            os.remove(db_path)
        except PermissionError:
            pass

def test_import_main_does_not_create_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        env = os.environ.copy()
        env["FRAMEWORK_DB_URL"] = f"sqlite:///{db_path}"
        script = f"""
import os
os.environ['FRAMEWORK_DB_URL'] = 'sqlite:///{db_path.replace(chr(92), '/')}'
from app.main import app
"""
        res = subprocess.run(["python", "-c", script], env=env, capture_output=True, text=True)
        assert res.returncode == 0
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        assert len(tables) == 0  # No tables should be created implicitly
        cursor.close()
        conn.close()
    finally:
        try:
            os.remove(db_path)
        except PermissionError:
            pass

def test_update_case_spaces_invalid():
    # Setup: Create a project and case
    client.post("/api/projects/", json={"name": "Proj Spaces", "description": "Proj"})
    case = client.post("/api/test-cases/", json={"name": "Valid Name", "sql_query": "SELECT 1 FROM dual", "expected_result": "1", "validation_type": "ROW_COUNT", "project_id": 1}).json()
    case_id = case["id"]
    
    # 7. Update name with spaces
    res = client.put(f"/api/test-cases/{case_id}", json={"name": "   "})
    assert res.status_code == 422
    
    # Check data intact
    res2 = client.get(f"/api/test-cases/{case_id}")
    assert res2.json()["name"] == "Valid Name"
    
    # 8. Update sql with spaces
    res3 = client.put(f"/api/test-cases/{case_id}", json={"sql_query": "   "})
    assert res3.status_code == 422
    
def test_update_case_invalid_combo():
    case = client.post("/api/test-cases/", json={"name": "Valid Combo", "sql_query": "SELECT 1 FROM dual", "expected_result": "TRUE", "validation_type": "EXISTS", "project_id": 1}).json()
    case_id = case["id"]
    
    # 9. Update to invalid combo
    # Update type to ROW_COUNT but keep expected_result='TRUE' which is invalid for ROW_COUNT
    res = client.put(f"/api/test-cases/{case_id}", json={"validation_type": "ROW_COUNT"})
    assert res.status_code == 422

def test_connection_profile_validations():
    # 10. Create profile with MYSQL
    res = client.post("/api/connections/", json={
        "project_id": 1,
        "name": "MySQL DB",
        "engine": "MYSQL",
        "host": "localhost",
        "port": 3306,
        "service_name": "db",
        "username": "root"
    })
    assert res.status_code == 422
    
    # 11. Create/Update with spaces
    res = client.post("/api/connections/", json={
        "project_id": 1,
        "name": "   ",
        "engine": "ORACLE",
        "host": "localhost",
        "port": 1521,
        "service_name": "db",
        "username": "root"
    })
    assert res.status_code == 422

def test_execution_integrity_checks():
    # Setup projects
    p1 = client.post("/api/projects/", json={"name": "P1"}).json()
    p2 = client.post("/api/projects/", json={"name": "P2"}).json()
    
    # Setup profile in p2
    prof = client.post("/api/connections/", json={
        "project_id": p2["id"],
        "name": "Prof P2",
        "engine": "ORACLE",
        "host": "localhost",
        "port": 1521,
        "service_name": "db",
        "username": "user"
    }).json()
    
    # Setup case in p1
    case = client.post("/api/test-cases/", json={
        "name": "Case P1",
        "sql_query": "SELECT 1 FROM dual",
        "expected_result": "1",
        "project_id": p1["id"]
    }).json()
    
    # 12. Execute case with profile of another project
    res = client.post(f"/api/execute/test-case/{case['id']}", json={
        "connection_profile_id": prof["id"],
        "password": "pwd"
    })
    assert res.status_code == 409
    
    # Setup suite in p1
    suite = client.post("/api/suites/", json={"name": "Suite P1", "project_id": p1["id"]}).json()
    client.post(f"/api/suites/{suite['id']}/test-cases/{case['id']}")
    
    # 13. Execute suite with profile of another project
    res = client.post(f"/api/execute/suite/{suite['id']}", json={
        "connection_profile_id": prof["id"],
        "password": "pwd"
    })
    assert res.status_code == 409

from unittest.mock import patch

@patch("app.api.executions.resolve_connection_credentials")
@patch("app.api.executions.TargetDatabaseExecutor")
def test_delete_project_with_history(mock_exec_cls, mock_resolve):
    p = client.post("/api/projects/", json={"name": "Proj Hist"}).json()
    prof = client.post("/api/connections/", json={
        "project_id": p["id"],
        "name": "Prof Hist",
        "engine": "ORACLE",
        "host": "localhost",
        "port": 1521,
        "service_name": "db",
        "username": "user"
    }).json()
    
    case = client.post("/api/test-cases/", json={"name": "Case Hist", "sql_query": "SELECT 1", "expected_result": "1", "project_id": p["id"]}).json()
    
    # Configurar mock
    from unittest.mock import MagicMock
    mock_prof = MagicMock()
    mock_prof.id = prof["id"]
    mock_resolve.return_value = ("dsn", "user", "pwd", mock_prof)
    mock_instance = mock_exec_cls.return_value
    mock_instance.execute_query.return_value = {
        "success": True,
        "statement_type": "SELECT",
        "rows": [{"1": 1}],
        "rowcount": 1,
        "rollback_applied": False,
        "rollback_error": None,
        "error_message": None
    }
    
    # Execute case to create history
    res = client.post(f"/api/execute/test-case/{case['id']}", json={
        "connection_profile_id": prof["id"],
        "password": "pwd"
    })
    assert res.status_code == 200
    
    # 14. Delete project with history
    res = client.delete(f"/api/projects/{p['id']}")
    assert res.status_code == 409

def test_history_status_filter():
    # 15. Filter history with invalid status
    res = client.get("/api/history/?status=INVALID")
    assert res.status_code == 422

def test_suite_editing():
    suite = client.post("/api/suites/", json={"name": "S1", "project_id": 1}).json()
    
    # 16. Edit suite
    res = client.put(f"/api/suites/{suite['id']}", json={"name": "S1 Edited"})
    assert res.status_code == 200
    assert res.json()["name"] == "S1 Edited"
    
def test_suite_remove_case():
    suite = client.post("/api/suites/", json={"name": "S2", "project_id": 1}).json()
    case = client.post("/api/test-cases/", json={"name": "C2", "sql_query": "A", "expected_result": "1", "project_id": 1}).json()
    client.post(f"/api/suites/{suite['id']}/test-cases/{case['id']}")
    
    # 17. Remove case
    res = client.delete(f"/api/suites/{suite['id']}/test-cases/{case['id']}")
    assert res.status_code == 204
    
    # Repeat operation
    res2 = client.delete(f"/api/suites/{suite['id']}/test-cases/{case['id']}")
    assert res2.status_code == 204 # Or handled gracefully

def test_startup_endpoints():
    # 20. Startup endpoints
    res = client.get("/")
    assert res.status_code == 200
    res = client.get("/docs")
    assert res.status_code == 200
    res = client.get("/openapi.json")
    assert res.status_code == 200

# Other scenarios (zip, passwords, legacy db migrations) are verified through CLI scripts or manually.
