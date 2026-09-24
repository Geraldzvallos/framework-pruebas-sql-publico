"""
Router de Ejecución de Pruebas SQL desacoplado utilizando el Servicio Centralizado de Ejecución.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import schemas
from app.models import test_case as models_tc
from app.models import suite as models_suite
from app.models import connection as models_conn
from app.engine.executor import TargetDatabaseExecutor
from app.services.execution_service import (
    resolve_connection_credentials,
    run_single_test_case_execution
)

router = APIRouter()

@router.post("/execute/raw", response_model=schemas.ExecutionResponse)
def execute_target_sql(request: schemas.ExecutionRequest, db: Session = Depends(get_db)):
    """Ejecuta una sentencia SQL aislada sin validación (Prueba de conexión/Sintaxis)."""
    try:
        dsn, user, password, _ = resolve_connection_credentials(
            db,
            connection_profile_id=request.connection_profile_id,
            dsn=request.dsn,
            user=request.user,
            password=request.password
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    executor = TargetDatabaseExecutor(dsn=dsn, user=user, password=password, environment_type="TEST")
    try:
        res = executor.execute_query(request.sql_query)
        if not res["success"]:
            detail_msg = res.get("message") or res.get("error_message") or "Error en ejecución SQL."
            raise HTTPException(status_code=400, detail=detail_msg)
        return schemas.ExecutionResponse(
            success=res["success"],
            statement_type=res["statement_type"],
            rows=res["rows"],
            rowcount=res["rowcount"],
            data=res["rows"],
            message=res["message"],
            error_message=res.get("error_message"),
            rollback_applied=res.get("rollback_applied", False),
            rollback_error=res.get("rollback_error")
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno no controlado durante la ejecución SQL.")
    finally:
        executor.disconnect()


@router.post("/execute/test-case/{test_case_id}", response_model=schemas.HistoryResponse)
def run_test_case(test_case_id: int, db_credentials: schemas.TestCaseExecutionRequest, db: Session = Depends(get_db)):
    """
    Orquestador Principal: Recupera un caso de prueba guardado y lo ejecuta
    utilizando el servicio centralizado de ejecución.
    """
    tc = db.query(models_tc.TestCase).filter(models_tc.TestCase.id == test_case_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="Caso de prueba no encontrado.")

    if db_credentials.connection_profile_id:
        profile = db.query(models_conn.ConnectionProfile).filter(models_conn.ConnectionProfile.id == db_credentials.connection_profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Perfil de conexión no encontrado.")
        if profile.project_id != tc.project_id:
            raise HTTPException(status_code=409, detail="El perfil de conexión no pertenece al proyecto del caso de prueba.")

    try:
        dsn, user, password, profile = resolve_connection_credentials(
            db,
            connection_profile_id=db_credentials.connection_profile_id,
            dsn=db_credentials.dsn,
            user=db_credentials.user,
            password=db_credentials.password
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    profile_id = profile.id if profile else db_credentials.connection_profile_id
    env_type = profile.environment_type if profile else "TEST"
    executor = TargetDatabaseExecutor(dsn=dsn, user=user, password=password, environment_type=env_type)
    
    try:
        history_record = run_single_test_case_execution(
            db=db,
            tc=tc,
            executor=executor,
            suite_id=None,
            connection_profile_id=profile_id
        )
        return history_record
    finally:
        executor.disconnect()


@router.post("/execute/suite/{suite_id}", response_model=schemas.SuiteExecutionSummary)
def run_test_suite(suite_id: int, db_credentials: schemas.SuiteExecutionRequest, db: Session = Depends(get_db)):
    """
    Ejecuta en ráfaga todos los casos de prueba de una Suite utilizando una conexión única.
    """
    suite = db.query(models_suite.TestSuite).filter(models_suite.TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Suite no encontrada.")
        
    if db_credentials.connection_profile_id:
        profile = db.query(models_conn.ConnectionProfile).filter(models_conn.ConnectionProfile.id == db_credentials.connection_profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Perfil de conexión no encontrado.")
        if profile.project_id != suite.project_id:
            raise HTTPException(status_code=409, detail="El perfil de conexión no pertenece al proyecto de la suite.")

    # Verificación de integridad: todos los casos de la suite deben pertenecer al mismo proyecto
    for tc in suite.test_cases:
        if tc.project_id != suite.project_id:
            raise HTTPException(status_code=409, detail=f"Inconsistencia: el caso de prueba {tc.id} no pertenece al proyecto {suite.project_id}.")

    summary = schemas.SuiteExecutionSummary(
        suite_id=suite.id,
        suite_name=suite.name,
        total_tests=len(suite.test_cases),
        passed=0, failed=0, errors=0, total_duration_ms=0.0
    )

    if summary.total_tests == 0:
        return summary

    try:
        dsn, user, password, profile = resolve_connection_credentials(
            db,
            connection_profile_id=db_credentials.connection_profile_id,
            dsn=db_credentials.dsn,
            user=db_credentials.user,
            password=db_credentials.password
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    profile_id = profile.id if profile else db_credentials.connection_profile_id
    env_type = profile.environment_type if profile else "TEST"
    executor = TargetDatabaseExecutor(dsn=dsn, user=user, password=password, environment_type=env_type)

    try:
        for tc in suite.test_cases:
            history_record = run_single_test_case_execution(
                db=db,
                tc=tc,
                executor=executor,
                suite_id=suite.id,
                connection_profile_id=profile_id
            )
            
            summary.total_duration_ms += history_record.duration_ms
            if history_record.status == "PASS":
                summary.passed += 1
            elif history_record.status == "FAIL":
                summary.failed += 1
            else:
                summary.errors += 1
                
            summary.details.append(history_record)

    finally:
        executor.disconnect()

    summary.total_duration_ms = round(summary.total_duration_ms, 2)
    return summary