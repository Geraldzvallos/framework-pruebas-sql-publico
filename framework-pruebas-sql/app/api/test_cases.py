"""
Endpoints REST para la gestión de Casos de Prueba SQL.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import test_case as models_tc
from app.models import project as models_project
from app.models import schemas
from app.services.project_service import ensure_default_project

router = APIRouter()

@router.post("/test-cases/", response_model=schemas.TestCaseResponse, status_code=201)
def create_test_case(test_case: schemas.TestCaseCreate, db: Session = Depends(get_db)):
    """Crea un nuevo caso de prueba asignado a un proyecto."""
    ensure_default_project(db)
    
    project_id = test_case.project_id or 1
    project = db.query(models_project.Project).filter(models_project.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Proyecto ID {project_id} no encontrado.")

    data = test_case.model_dump()
    data["project_id"] = project_id
    db_test_case = models_tc.TestCase(**data)
    
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    
    return db_test_case

@router.get("/test-cases/", response_model=list[schemas.TestCaseResponse])
def read_test_cases(
    project_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obtiene la lista de casos de prueba guardados con paginación y filtro de proyecto."""
    query = db.query(models_tc.TestCase)
    if project_id:
        query = query.filter(models_tc.TestCase.project_id == project_id)
    test_cases = query.offset(skip).limit(limit).all()
    return test_cases

@router.get("/test-cases/{test_case_id}", response_model=schemas.TestCaseResponse)
def read_test_case(test_case_id: int, db: Session = Depends(get_db)):
    """Obtiene un caso de prueba específico por su ID."""
    db_tc = db.query(models_tc.TestCase).filter(models_tc.TestCase.id == test_case_id).first()
    if not db_tc:
        raise HTTPException(status_code=404, detail="Caso de prueba no encontrado.")
    return db_tc

@router.put("/test-cases/{test_case_id}", response_model=schemas.TestCaseResponse)
def update_test_case(test_case_id: int, tc_update: schemas.TestCaseUpdate, db: Session = Depends(get_db)):
    """Actualiza la información de un caso de prueba."""
    db_tc = db.query(models_tc.TestCase).filter(models_tc.TestCase.id == test_case_id).first()
    if not db_tc:
        raise HTTPException(status_code=404, detail="Caso de prueba no encontrado.")

    update_data = tc_update.model_dump(exclude_unset=True)
    if update_data:
        merged_data = {
            "project_id": db_tc.project_id,
            "name": db_tc.name,
            "description": db_tc.description,
            "sql_query": db_tc.sql_query,
            "validation_type": getattr(schemas.ValidationTypeEnum, db_tc.validation_type) if isinstance(db_tc.validation_type, str) else db_tc.validation_type,
            "expected_result": db_tc.expected_result,
        }
        merged_data.update(update_data)
        
        from pydantic import ValidationError
        try:
            schemas.TestCaseCreate(**merged_data)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=str(e))

        for key, value in update_data.items():
            # Extraer valor si es Enum
            if isinstance(value, schemas.ValidationTypeEnum):
                value = value.value
            setattr(db_tc, key, value)

    db.commit()
    db.refresh(db_tc)
    return db_tc

@router.delete("/test-cases/{test_case_id}", status_code=204)
def delete_test_case(test_case_id: int, db: Session = Depends(get_db)):
    """Elimina un caso de prueba de la base de datos."""
    db_tc = db.query(models_tc.TestCase).filter(models_tc.TestCase.id == test_case_id).first()
    if not db_tc:
        raise HTTPException(status_code=404, detail="Caso de prueba no encontrado.")
    
    db.delete(db_tc)
    db.commit()
    return
