"""
Módulo de ejecución SQL para el Framework de Pruebas.
Gestiona la conectividad y el aislamiento transaccional sobre SGBDs relacionales.
"""
import sqlparse
from sqlparse.tokens import Whitespace, Comment as CommentToken, String, Keyword, DDL, DML
import oracledb
from typing import Any, Dict, List, Tuple, Optional

import os
from app.security.sql_policy import validate_sql_statement


class TargetDatabaseExecutor:
    """
    Administra la sesión con la base de datos objetivo (Oracle) garantizando 
    el cumplimiento de las restricciones de seguridad (ej. Rollback por defecto).
    """
    
    def __init__(self, dsn: str, user: str, password: str, environment_type: str = "TEST"):
        self.dsn = dsn
        self.user = user
        self.password = password
        self.environment_type = environment_type
        self._connection: Optional[oracledb.Connection] = None
        self.max_rows = int(os.getenv("MAX_RESULT_ROWS", "1000"))
        self.timeout_ms = int(os.getenv("ORACLE_CALL_TIMEOUT_MS", "10000"))

    def connect(self) -> None:
        """Establece la conexión utilizando oracledb en modo thin."""
        self._connection = oracledb.connect(
            user=self.user,
            password=self.password,
            dsn=self.dsn
        )
        if hasattr(self._connection, 'call_timeout'):
            self._connection.call_timeout = self.timeout_ms
        self._connection.autocommit = False

    def _sanitize_message(self, msg: str) -> str:
        """Remueve cualquier rastro de la contraseña de los mensajes de error/logs."""
        if self.password and self.password in msg:
            return msg.replace(self.password, "******")
        return msg

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ejecuta una sentencia SQL aislada y devuelve una estructura de respuesta estandarizada.
        
        Args:
            query: Sentencia SQL a procesar.
            params: Diccionario de parámetros para binding seguro.
            
        Returns:
            Dict[str, Any]: Estructura estandarizada con success, statement_type, rows, rowcount, message, error_message, rollback_applied, rollback_error.
        """
        is_valid, stmt_type, validation_error = validate_sql_statement(query, self.environment_type)
        if not is_valid:
            return {
                "success": False,
                "statement_type": stmt_type,
                "rows": [],
                "rowcount": 0,
                "message": validation_error,
                "error_message": validation_error,
                "rollback_applied": False,
                "rollback_error": None
            }

        try:
            if not self._connection:
                self.connect()
        except Exception as e:
            err_msg = self._sanitize_message(str(e))
            return {
                "success": False,
                "statement_type": stmt_type,
                "rows": [],
                "rowcount": 0,
                "message": "Error al conectar con la base de datos objetivo.",
                "error_message": err_msg,
                "rollback_applied": False,
                "rollback_error": None
            }

        cursor = None
        exec_error = None
        fetched_rows = []
        row_count = 0
        query_success = False

        try:
            cursor = self._connection.cursor()
            cleaned_sql = query.strip().rstrip(";").strip()
            cursor.execute(cleaned_sql, params or {})

            if stmt_type == "SELECT":
                fetched_rows = cursor.fetchmany(self.max_rows)
                row_count = len(fetched_rows)
                query_success = True
            else:
                row_count = cursor.rowcount
                query_success = True

        except Exception as e:
            exec_error = self._sanitize_message(str(e))
            query_success = False

        # Gestión estricta y transparente de Rollback
        rollback_applied = False
        rollback_error = None

        if stmt_type in {"INSERT", "UPDATE", "DELETE"} or not query_success:
            if self._connection:
                try:
                    self._connection.rollback()
                    if stmt_type in {"INSERT", "UPDATE", "DELETE"} and query_success:
                        rollback_applied = True
                except Exception as rb_exc:
                    rollback_applied = False
                    rollback_error = self._sanitize_message(str(rb_exc))

        # Cierre seguro del cursor
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass

        if not query_success:
            return {
                "success": False,
                "statement_type": stmt_type,
                "rows": [],
                "rowcount": 0,
                "message": f"Fallo en la ejecución de la sentencia {stmt_type}.",
                "error_message": exec_error,
                "rollback_applied": rollback_applied,
                "rollback_error": rollback_error
            }

        if stmt_type == "SELECT":
            return {
                "success": True,
                "statement_type": stmt_type,
                "rows": fetched_rows,
                "rowcount": row_count,
                "message": f"Consulta SELECT ejecutada exitosamente. {row_count} filas recuperadas.",
                "error_message": None,
                "rollback_applied": False,
                "rollback_error": None
            }

        # Control del resultado DML cuando falla el rollback
        if rollback_error is not None or not rollback_applied:
            return {
                "success": False,
                "statement_type": stmt_type,
                "rows": [],
                "rowcount": row_count,
                "message": f"Fallo al aplicar rollback transaccional en operación {stmt_type}.",
                "error_message": f"Error de rollback: {rollback_error}" if rollback_error else "El rollback transaccional no pudo ser verificado.",
                "rollback_applied": False,
                "rollback_error": rollback_error
            }

        return {
            "success": True,
            "statement_type": stmt_type,
            "rows": [],
            "rowcount": row_count,
            "message": f"Operación {stmt_type} procesada exitosamente. {row_count} filas afectadas. Rollback aplicado.",
            "error_message": None,
            "rollback_applied": True,
            "rollback_error": None
        }

    def disconnect(self) -> None:
        """Libera los recursos de conexión activos."""
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            finally:
                self._connection = None