"""
Servicio centralizado de ejecución y validación de pruebas SQL.
Garantiza que la ejecución individual y la de suites compartan la misma lógica de orquestación y trazabilidad.
"""
import time
import json
from decimal import Decimal
from datetime import datetime, date
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session
import oracledb

from app.engine.executor import TargetDatabaseExecutor
from app.engine.validator import ValidationContext, RowCountValidation, ExistenceValidation
from app.models import test_case as models_tc
from app.models import history as models_history
from app.models import connection as models_conn


def json_serial_helper(obj: Any) -> Any:
    """Helper para convertir objetos no JSON nativos habituales en Oracle."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    return str(obj)


def format_actual_result(rows: Any, max_chars: int = 2000) -> str:
    """Serializa y limita el tamaño del resultado real devuelto como evidencia."""
    try:
        serialized = json.dumps(rows, default=json_serial_helper, ensure_ascii=False)
        if len(serialized) > max_chars:
            return serialized[:max_chars] + " ... [TRUNCADO]"
        return serialized
    except Exception as e:
        return f"[Error serializando resultado: {str(e)}]"


def resolve_connection_credentials(
    db: Session,
    connection_profile_id: Optional[int] = None,
    dsn: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None
) -> Tuple[str, str, str, Optional[models_conn.ConnectionProfile]]:
    """
    Resuelve el DSN, usuario y objeto profile a partir de connection_profile_id o de credenciales directas.
    """
    if not password:
        raise ValueError("Se requiere una contraseña para ejecutar la prueba.")

    profile = None
    if connection_profile_id:
        profile = db.query(models_conn.ConnectionProfile).filter(models_conn.ConnectionProfile.id == connection_profile_id).first()
        if not profile:
            raise ValueError(f"Perfil de conexión ID {connection_profile_id} no encontrado.")
        resolved_dsn = oracledb.makedsn(profile.host, profile.port, service_name=profile.service_name)
        resolved_user = profile.username
    elif dsn and user:
        resolved_dsn = dsn
        resolved_user = user
    else:
        raise ValueError("Debe proporcionar un connection_profile_id o dsn y user válidos.")

    return resolved_dsn, resolved_user, password, profile


def run_single_test_case_execution(
    db: Session,
    tc: models_tc.TestCase,
    executor: TargetDatabaseExecutor,
    suite_id: Optional[int] = None,
    connection_profile_id: Optional[int] = None
) -> models_history.ExecutionHistory:
    """
    Servicio central que ejecuta un caso de prueba contra la BD objetivo,
    evalúa el resultado según la estrategia elegida y persiste la evidencia.
    """
    start_time = time.time()
    status = "ERROR"
    error_msg = None
    
    # 1. Ejecución del SQL contra la BD objetivo
    res = executor.execute_query(tc.sql_query)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    
    stmt_type = res.get("statement_type", "UNKNOWN")
    rowcount = res.get("rowcount", 0)
    rows = res.get("rows", [])
    rollback_applied = res.get("rollback_applied", False)
    rollback_error = res.get("rollback_error")
    
    if getattr(executor, 'environment_type', 'TEST') == "PRODUCTION":
        actual_result_str = format_actual_result(f"Operación exitosa. {rowcount} filas leídas.") if stmt_type == "SELECT" else format_actual_result(f"Filas afectadas: {rowcount}")
    else:
        actual_result_str = format_actual_result(rows if stmt_type == "SELECT" else f"Filas afectadas: {rowcount}")

    # 2. Evaluación del resultado
    if not res.get("success", False):
        status = "ERROR"
        error_msg = res.get("error_message") or res.get("message")
    elif stmt_type in {"INSERT", "UPDATE", "DELETE"} and not rollback_applied:
        # Falso rollback en DML produce ERROR
        status = "ERROR"
        error_msg = res.get("error_message") or "El rollback transaccional falló o no fue verificado."
    else:
        # Selección de estrategia
        val_type = (tc.validation_type or "ROW_COUNT").upper()
        if val_type == "EXISTS":
            strategy = ExistenceValidation()
        else:
            strategy = RowCountValidation()
            
        validator = ValidationContext(strategy)
        is_valid = validator.execute_validation(res, tc.expected_result)
        status = "PASS" if is_valid else "FAIL"

    # 3. Persistir evidencia en ExecutionHistory
    history_record = models_history.ExecutionHistory(
        project_id=tc.project_id,
        test_case_id=tc.id,
        suite_id=suite_id,
        connection_profile_id=connection_profile_id,
        status=status,
        duration_ms=duration_ms,
        statement_type=stmt_type,
        executed_sql=tc.sql_query,
        validation_type=tc.validation_type,
        expected_result=tc.expected_result,
        actual_result=actual_result_str,
        rowcount=rowcount,
        rollback_applied=rollback_applied,
        rollback_error=rollback_error,
        error_message=error_msg
    )
    
    db.add(history_record)
    db.commit()
    db.refresh(history_record)
    
    return history_record
