"""
Endpoints REST para las Suites de Pruebas.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.models import suite as models_suite
from app.models import test_case as models_tc
from app.models import project as models_project
from app.models import schemas
from app.services.project_service import ensure_default_project

router = APIRouter()

@router.post("/suites/", response_model=schemas.TestSuiteResponse, status_code=201)
def create_suite(suite: schemas.TestSuiteCreate, db: Session = Depends(get_db)):
    """Crea una nueva Suite de Pruebas."""
    ensure_default_project(db)
    
    project_id = suite.project_id or 1
    project = db.query(models_project.Project).filter(models_project.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Proyecto ID {project_id} no encontrado.")

    data = suite.model_dump()
    data["project_id"] = project_id
    db_suite = models_suite.TestSuite(**data)
    
    db.add(db_suite)
    db.commit()
    db.refresh(db_suite)
    return db_suite

@router.post("/suites/{suite_id}/test-cases/{test_case_id}", response_model=schemas.TestSuiteResponse)
def add_test_case_to_suite(suite_id: int, test_case_id: int, db: Session = Depends(get_db)):
    """
    Vincula un Caso de Prueba a una Suite de Pruebas.
    Validaciones estrictas:
    - 404 si la suite o el caso no existen.
    - 409 si el caso ya pertenece a la suite.
    - 409 si el caso y la suite pertenecen a proyectos distintos.
    """
    db_suite = db.query(models_suite.TestSuite).filter(models_suite.TestSuite.id == suite_id).first()
    if not db_suite:
        raise HTTPException(status_code=404, detail="Suite de prueba no encontrada.")

    db_tc = db.query(models_tc.TestCase).filter(models_tc.TestCase.id == test_case_id).first()
    if not db_tc:
        raise HTTPException(status_code=404, detail="Caso de prueba no encontrado.")

    if db_tc in db_suite.test_cases:
        raise HTTPException(status_code=409, detail=f"El caso de prueba #{test_case_id} ya pertenece a la suite #{suite_id}.")

    if db_tc.project_id != db_suite.project_id:
        raise HTTPException(
            status_code=409,
            detail=f"El caso (Proyecto {db_tc.project_id}) y la suite (Proyecto {db_suite.project_id}) pertenecen a proyectos distintos."
        )

    db_suite.test_cases.append(db_tc)
    db.commit()
    db.refresh(db_suite)
    
    return db_suite

@router.get("/suites/", response_model=list[schemas.TestSuiteResponse])
def get_all_suites(
    project_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obtiene todas las suites registradas con paginación y filtro de proyecto."""
    query = db.query(models_suite.TestSuite)
    if project_id:
        query = query.filter(models_suite.TestSuite.project_id == project_id)
    suites = query.offset(skip).limit(limit).all()
    return suites

@router.get("/suites/{suite_id}", response_model=schemas.TestSuiteResponse)
def get_suite_detail(suite_id: int, db: Session = Depends(get_db)):
    """Obtiene el detalle de una suite por su ID."""
    db_suite = db.query(models_suite.TestSuite).filter(models_suite.TestSuite.id == suite_id).first()
    if not db_suite:
        raise HTTPException(status_code=404, detail="Suite de prueba no encontrada.")
    return db_suite

@router.delete("/suites/{suite_id}", status_code=204)
def delete_suite(suite_id: int, db: Session = Depends(get_db)):
    """Elimina una suite de prueba."""
    db_suite = db.query(models_suite.TestSuite).filter(models_suite.TestSuite.id == suite_id).first()
    if not db_suite:
        raise HTTPException(status_code=404, detail="Suite de prueba no encontrada.")
    try:
        db.delete(db_suite)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No se puede eliminar la suite porque está referenciada en el historial u otras tablas.")
    return

@router.put("/suites/{suite_id}", response_model=schemas.TestSuiteResponse)
def update_suite(suite_id: int, suite_update: schemas.TestSuiteUpdate, db: Session = Depends(get_db)):
    """Actualiza nombre y descripción de una suite."""
    db_suite = db.query(models_suite.TestSuite).filter(models_suite.TestSuite.id == suite_id).first()
    if not db_suite:
        raise HTTPException(status_code=404, detail="Suite de prueba no encontrada.")
    
    update_data = suite_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_suite, key, value)
    
    db.commit()
    db.refresh(db_suite)
    return db_suite

@router.delete("/suites/{suite_id}/test-cases/{test_case_id}", status_code=204)
def remove_test_case_from_suite(suite_id: int, test_case_id: int, db: Session = Depends(get_db)):
    """Retira un caso de una suite de forma controlada."""
    db_suite = db.query(models_suite.TestSuite).filter(models_suite.TestSuite.id == suite_id).first()
    if not db_suite:
        raise HTTPException(status_code=404, detail="Suite de prueba no encontrada.")
    
    db_tc = db.query(models_tc.TestCase).filter(models_tc.TestCase.id == test_case_id).first()
    if not db_tc:
        raise HTTPException(status_code=404, detail="Caso de prueba no encontrado.")
        
    if db_tc in db_suite.test_cases:
        db_suite.test_cases.remove(db_tc)
        db.commit()
    return
