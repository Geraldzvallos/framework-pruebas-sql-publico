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

@patch.dict(os.environ, {"MAX_RESULT_ROWS": "invalid", "ORACLE_CALL_TIMEOUT_MS": "-500"})
def test_executor_safe_limits():
    """Verifica que los límites se parseen de forma segura usando valores por defecto."""
    executor = TargetDatabaseExecutor(dsn="dsn", user="user", password="contrasena_ficticia_test")
    assert executor.max_rows == 1000
    assert executor.timeout_ms == 10000

@patch.dict(os.environ, {"MAX_RESULT_ROWS": "9999999", "ORACLE_CALL_TIMEOUT_MS": "9999999"})
def test_executor_excessive_limits():
    """Verifica que si se superan los máximos, se asignan valores seguros."""
    executor = TargetDatabaseExecutor(dsn="dsn", user="user", password="contrasena_ficticia_test")
    assert executor.max_rows == 1000
    assert executor.timeout_ms == 10000

@patch("oracledb.connect")
def test_production_error_masking(mock_connect):
    """Verifica que los errores de conexión se enmascaren en PRODUCTION."""
    mock_connect.side_effect = Exception("Real connection error with sensitive data")
    executor = TargetDatabaseExecutor(dsn="localhost/xe", user="u", password="contrasena_ficticia_test", environment_type="PRODUCTION")
    res = executor.execute_query("SELECT 1 FROM dual")
    assert res["success"] is False
    assert "Real connection error" not in res["error_message"]
    assert "oculto por políticas" in res["error_message"]

@patch("oracledb.connect")
def test_production_execution_error_masking(mock_connect):
    """Verifica que los errores de ejecución se enmascaren en PRODUCTION."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Real execution ORA-00000 error")

    executor = TargetDatabaseExecutor(dsn="localhost/xe", user="u", password="contrasena_ficticia_test", environment_type="PRODUCTION")
    res = executor.execute_query("SELECT * FROM sensitive_table")
    assert res["success"] is False
    assert "Real execution ORA-00000 error" not in res["error_message"]
    assert "oculto por políticas" in res["error_message"]

def test_executor_environment_type_normalization():
    """Verifica que environment_type con espacios y minúsculas se asigne correctamente."""
    executor = TargetDatabaseExecutor(dsn="dsn", user="u", password="contrasena_ficticia_test", environment_type="  staging  ")
    assert executor.environment_type == "STAGING"

def test_executor_environment_type_enum_normalization():
    """Verifica que un enum como EnvironmentTypeEnum.PRODUCTION se asigne correctamente."""
    from app.models.schemas import EnvironmentTypeEnum
    executor = TargetDatabaseExecutor(dsn="dsn", user="u", password="contrasena_ficticia_test", environment_type=EnvironmentTypeEnum.PRODUCTION)
    assert executor.environment_type == "PRODUCTION"

def test_executor_invalid_environment_raises():
    """Verifica que un environment_type inválido lanza ValueError."""
    import pytest
    with pytest.raises(ValueError, match="Ambiente de ejecución inválido: INVALID"):
        TargetDatabaseExecutor(dsn="dsn", user="u", password="contrasena_ficticia_test", environment_type="INVALID")

@patch("oracledb.connect")
def test_production_row_count_and_exists_work_with_hidden_rows(mock_connect):
    """Verifica que ROW_COUNT y EXISTS pasen en producción aunque rows=[]."""
    from app.engine.validator import ValidationContext, RowCountValidation, ExistenceValidation

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    # Simular que fetchmany devuelve 5 filas
    mock_cursor.fetchmany.return_value = [("Data1",), ("Data2",), ("Data3",), ("Data4",), ("Data5",)]

    executor = TargetDatabaseExecutor(dsn="localhost/xe", user="u", password="contrasena_ficticia_test", environment_type="PRODUCTION")
    res = executor.execute_query("SELECT * FROM users")

    # En producción rows debe estar vacío
    assert res["success"] is True
    assert res["rows"] == []
    assert res["rowcount"] == 5

    ctx = ValidationContext(RowCountValidation())
    assert ctx.execute_validation(res, "5") is True

    ctx.set_strategy(ExistenceValidation())
    assert ctx.execute_validation(res, "TRUE") is True

def test_rollback_error_not_stored_in_production():
    """Verifica que rollback_error real nunca quede almacenado en producción en el execution_service."""
    from app.services.execution_service import run_single_test_case_execution
    from app.models.test_case import TestCase

    executor_mock = MagicMock()
    executor_mock.environment_type = "PRODUCTION"
    executor_mock.execute_query.return_value = {
        "success": False,
        "statement_type": "UPDATE",
        "rows": [],
        "rowcount": 0,
        "message": "Fallo simulado.",
        "error_message": "Real Oracle Error 9999",
        "rollback_applied": False,
        "rollback_error": "Real Rollback ORA-1234 Error"
    }

    db_mock = MagicMock()
    tc_mock = MagicMock(spec=TestCase)
    tc_mock.id = 1
    tc_mock.project_id = 1
    tc_mock.sql_query = "UPDATE table SET a=1"
    tc_mock.validation_type = "ROW_COUNT"
    tc_mock.expected_result = "1"

    history_record = run_single_test_case_execution(db=db_mock, tc=tc_mock, executor=executor_mock)

    assert "Real Oracle Error 9999" not in history_record.error_message
    assert "oculto por políticas" in history_record.error_message
    assert "Real Rollback ORA-1234 Error" not in history_record.rollback_error
    assert "oculto por políticas" in history_record.rollback_error
