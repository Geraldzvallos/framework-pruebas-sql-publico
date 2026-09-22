"""
Endpoints REST para la consulta del Historial de Ejecuciones.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import history as models_history
from app.models import schemas

router = APIRouter()

@router.get("/history/", response_model=list[schemas.HistoryResponse])
def get_history(
    project_id: Optional[int] = Query(None),
    test_case_id: Optional[int] = Query(None),
    suite_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de ejecuciones guardadas admitiendo paginación
    y filtros opcionales por project_id, test_case_id, suite_id y status.
    """
    query = db.query(models_history.ExecutionHistory)
    
    if project_id:
        query = query.filter(models_history.ExecutionHistory.project_id == project_id)
    if test_case_id:
        query = query.filter(models_history.ExecutionHistory.test_case_id == test_case_id)
    if suite_id:
        query = query.filter(models_history.ExecutionHistory.suite_id == suite_id)
    if status:
        status = status.upper()
        if status not in ["PASS", "FAIL", "ERROR"]:
            raise HTTPException(status_code=422, detail="Estado inválido. Use PASS, FAIL o ERROR.")
        query = query.filter(models_history.ExecutionHistory.status == status)

    histories = query.order_by(models_history.ExecutionHistory.id.desc()).offset(skip).limit(limit).all()
    return histories

@router.get("/history/{history_id}", response_model=schemas.HistoryResponse)
def get_history_detail(history_id: int, db: Session = Depends(get_db)):
    """Obtiene los detalles de un registro de historial específico."""
    record = db.query(models_history.ExecutionHistory).filter(models_history.ExecutionHistory.id == history_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Registro de historial no encontrado.")
    return record
