import pytest
from app.security.sql_policy import validate_sql_statement

def test_sql_policy_test_env():
    # Permitidas
    assert validate_sql_statement("SELECT * FROM users", "TEST")[0] is True
    assert validate_sql_statement("INSERT INTO users (name) VALUES ('a')", "TEST")[0] is True
    assert validate_sql_statement("UPDATE users SET name='b'", "TEST")[0] is True
    assert validate_sql_statement("DELETE FROM users", "TEST")[0] is True

    # Bloqueadas (DDL, TCL, MULTIPLE)
    assert validate_sql_statement("DROP TABLE users", "TEST")[0] is False
    assert validate_sql_statement("COMMIT", "TEST")[0] is False
    assert validate_sql_statement("SELECT * FROM users; DROP TABLE users;", "TEST")[0] is False
    assert validate_sql_statement("BEGIN DBMS_OUTPUT.PUT_LINE('a'); END;", "TEST")[0] is False

def test_sql_policy_staging_env():
    # Iguales reglas que TEST, DML es interceptado en UI
    assert validate_sql_statement("SELECT * FROM users", "STAGING")[0] is True
    assert validate_sql_statement("INSERT INTO users (name) VALUES ('a')", "STAGING", True)[0] is True
    assert validate_sql_statement("UPDATE users SET name='b'", "STAGING", True)[0] is True
    assert validate_sql_statement("DELETE FROM users", "STAGING", True)[0] is True

    # Bloqueadas (DDL, TCL, MULTIPLE)
    assert validate_sql_statement("DROP TABLE users", "STAGING")[0] is False

def test_sql_policy_production_env():
    # Solo SELECT permitido
    assert validate_sql_statement("SELECT * FROM users", "PRODUCTION")[0] is True
    assert validate_sql_statement("WITH cte AS (SELECT 1 FROM dual) SELECT * FROM cte", "PRODUCTION")[0] is True

    # Bloqueadas explícitamente en PRODUCTION (DML)
    assert validate_sql_statement("INSERT INTO users (name) VALUES ('a')", "PRODUCTION")[0] is False
    assert validate_sql_statement("UPDATE users SET name='b'", "PRODUCTION")[0] is False
    assert validate_sql_statement("DELETE FROM users", "PRODUCTION")[0] is False

    # Bloqueadas (DDL, TCL, MULTIPLE)
    assert validate_sql_statement("DROP TABLE users", "PRODUCTION")[0] is False
    assert validate_sql_statement("COMMIT", "PRODUCTION")[0] is False

def test_sql_policy_literals_ignored():
    # La validación no debería bloquear por palabras prohibidas dentro de literales de texto
    is_valid, stmt_type, error = validate_sql_statement("SELECT 'DROP TABLE' FROM DUAL", "TEST")
    assert is_valid is True
    assert stmt_type == "SELECT"

    is_valid, stmt_type, error = validate_sql_statement("SELECT 'COMMIT' FROM DUAL", "PRODUCTION")
    assert is_valid is True

def test_sql_policy_empty_or_comments():
    assert validate_sql_statement("   ", "TEST")[0] is False
    assert validate_sql_statement("-- Solo un comentario", "TEST")[0] is False

    is_valid, stmt_type, _ = validate_sql_statement("-- Comentario \n SELECT 1 FROM DUAL", "TEST")
    assert is_valid is True
    assert stmt_type == "SELECT"

def test_sql_policy_invalid_env():
    """Verifica que un ambiente inválido sea rechazado."""
    is_valid, stmt_type, msg = validate_sql_statement("SELECT 1 FROM DUAL", "INVALID")
    assert is_valid is False
    assert "inválido" in msg.lower()
