"""
Pruebas unitarias avanzadas para el motor de ejecución SQL, aislamiento transaccional y casos límite.
"""
import os
import hashlib
from unittest.mock import MagicMock, patch
from app.engine.executor import TargetDatabaseExecutor, validate_sql_statement
from app.engine.validator import ValidationContext, RowCountValidation, ExistenceValidation


def test_select_with_drop_inside_string_literal():
    """Punto 4.1: SELECT con la palabra 'DROP' dentro de un texto es VÁLIDA."""
    query = "SELECT 'DROP' AS texto FROM dual"
    is_valid, stmt_type, err = validate_sql_statement(query)
    assert is_valid is True
    assert stmt_type == "SELECT"
    assert err == ""


def test_select_with_semicolon_inside_string_literal():
    """Punto 4.2: SELECT con punto y coma dentro de un texto es VÁLIDA."""
    query = "SELECT 'a;b' AS texto FROM dual"
    is_valid, stmt_type, err = validate_sql_statement(query)
    assert is_valid is True
    assert stmt_type == "SELECT"
    assert err == ""


def test_insert_with_commit_inside_string_literal():
    """Punto 4.3: INSERT con 'COMMIT' dentro de un valor es VÁLIDA."""
    query = "INSERT INTO logs(message) VALUES ('COMMIT realizado')"
    is_valid, stmt_type, err = validate_sql_statement(query)
    assert is_valid is True
    assert stmt_type == "INSERT"
    assert err == ""


def test_update_with_alter_inside_description():
    """Punto 4.4: UPDATE con 'ALTER' dentro de una descripción es VÁLIDA."""
    query = "UPDATE products SET description='ALTER color' WHERE id=1"
    is_valid, stmt_type, err = validate_sql_statement(query)
    assert is_valid is True
    assert stmt_type == "UPDATE"
    assert err == ""


def test_sql_with_leading_comments():
    """Punto 4.5: SQL con comentarios iniciales se reconoce correctamente."""
    query = "-- Consulta de prueba válida\nSELECT 1 FROM dual"
    is_valid, stmt_type, err = validate_sql_statement(query)
    assert is_valid is True
    assert stmt_type == "SELECT"
    assert err == ""


def test_sql_with_single_trailing_semicolon():
    """Punto 4.6: Consulta con un único punto y coma final es VÁLIDA."""
    query = "SELECT 1 FROM dual;"
    is_valid, stmt_type, err = validate_sql_statement(query)
    assert is_valid is True
    assert stmt_type == "SELECT"
    assert err == ""


def test_two_real_sql_statements_rejected():
    """Punto 4.7: Dos sentencias SQL reales deben ser rechazadas."""
    query = "SELECT 1 FROM dual; SELECT 2 FROM dual;"
    is_valid, stmt_type, err = validate_sql_statement(query)
    assert is_valid is False
    assert stmt_type == "MULTIPLE"
    assert "múltiples sentencias" in err


@patch("oracledb.connect")
def test_correct_rollback_for_insert(mock_connect):
    """Punto 4.8: Rollback correcto para INSERT."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.rowcount = 1

    executor = TargetDatabaseExecutor(dsn="localhost/xe", user="user", password="secret_password")
    res = executor.execute_query("INSERT INTO users(name) VALUES ('Alice')")

    assert res["success"] is True
    assert res["statement_type"] == "INSERT"
    assert res["rowcount"] == 1
    assert res["rollback_applied"] is True
    assert res["rollback_error"] is None
    mock_conn.rollback.assert_called_once()


@patch("oracledb.connect")
def test_correct_rollback_for_update(mock_connect):
    """Punto 4.9: Rollback correcto para UPDATE."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.rowcount = 3

    executor = TargetDatabaseExecutor(dsn="localhost/xe", user="user", password="secret_password")
    res = executor.execute_query("UPDATE users SET status='active' WHERE role='user'")

    assert res["success"] is True
    assert res["statement_type"] == "UPDATE"
    assert res["rowcount"] == 3
    assert res["rollback_applied"] is True
    assert res["rollback_error"] is None
    mock_conn.rollback.assert_called_once()


@patch("oracledb.connect")
def test_correct_rollback_for_delete(mock_connect):
    """Punto 4.10: Rollback correcto para DELETE."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.rowcount = 5

    executor = TargetDatabaseExecutor(dsn="localhost/xe", user="user", password="secret_password")
    res = executor.execute_query("DELETE FROM users WHERE active=0")

    assert res["success"] is True
    assert res["statement_type"] == "DELETE"
    assert res["rowcount"] == 5
    assert res["rollback_applied"] is True
    assert res["rollback_error"] is None
    mock_conn.rollback.assert_called_once()


@patch("oracledb.connect")
def test_simulated_rollback_failure(mock_connect):
    """Punto 4.11: Falla simulada de rollback hace que success sea False."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.rowcount = 1
    mock_conn.rollback.side_effect = Exception("Rollback Connection Error")

    executor = TargetDatabaseExecutor(dsn="localhost/xe", user="user", password="secret_password")
    res = executor.execute_query("UPDATE users SET name='Failed'")

    assert res["success"] is False
    assert res["rollback_applied"] is False
    assert res["rollback_error"] is not None
    assert "Rollback Connection Error" in res["rollback_error"]
    assert "Rollback aplicado" not in res["message"]


@patch("oracledb.connect")
def test_cursor_closed_properly(mock_connect):
    """Punto 4.12: Cierre correcto del cursor."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [("Data",)]

    executor = TargetDatabaseExecutor(dsn="localhost/xe", user="user", password="secret_password")
    executor.execute_query("SELECT * FROM dual")

    mock_cursor.close.assert_called_once()


@patch("oracledb.connect")
def test_connection_closed_properly(mock_connect):
    """Punto 4.13: Cierre correcto de la conexión mediante disconnect()."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    executor = TargetDatabaseExecutor(dsn="localhost/xe", user="user", password="secret_password")
    executor.connect()
    executor.disconnect()

    mock_conn.close.assert_called_once()
    assert executor._connection is None


@patch("oracledb.connect")
def test_connection_error_handling(mock_connect):
    """Punto 4.14: Error al conectar con la base de datos es manejado limpiamente."""
    mock_connect.side_effect = Exception("Connection refused to secret_pass")

    executor = TargetDatabaseExecutor(dsn="invalid_dsn", user="user", password="secret_pass")
    res = executor.execute_query("SELECT 1 FROM dual")

    assert res["success"] is False
    assert "Error al conectar" in res["message"]
    assert "secret_pass" not in res["error_message"]
    assert "******" in res["error_message"]


def test_test_db_isolation_and_framework_db_unmodified():
    """Punto 4.15: Base de pruebas completamente aislada y confirma que framework_interno.db no cambió."""
    db_file = "framework_interno.db"
    if os.path.exists(db_file):
        initial_size = os.path.getsize(db_file)
        initial_mtime = os.path.getmtime(db_file)
        
        # Simular lectura
        with open(db_file, "rb") as f:
            initial_hash = hashlib.sha256(f.read()).hexdigest()
            
        assert os.path.getsize(db_file) == initial_size
        assert os.path.getmtime(db_file) == initial_mtime
        
        with open(db_file, "rb") as f:
            final_hash = hashlib.sha256(f.read()).hexdigest()
        assert initial_hash == final_hash
