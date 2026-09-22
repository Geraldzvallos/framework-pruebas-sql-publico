"""
Endpoints REST para la gestión de Proyectos.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.models import project as models_project
from app.models import schemas

router = APIRouter()

@router.post("/projects/", response_model=schemas.ProjectResponse, status_code=201)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """Crea un nuevo proyecto."""
    existing = db.query(models_project.Project).filter(models_project.Project.name == project.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Ya existe un proyecto registrado con el nombre '{project.name}'.")

    db_project = models_project.Project(**project.model_dump())
    db.add(db_project)
    try:
        db.commit()
        db.refresh(db_project)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Error de integridad al crear el proyecto.")
    return db_project

@router.get("/projects/", response_model=list[schemas.ProjectResponse])
def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obtiene la lista de proyectos con paginación estricta."""
    projects = db.query(models_project.Project).offset(skip).limit(limit).all()
    return projects

@router.get("/projects/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Obtiene los detalles de un proyecto por su ID."""
    db_project = db.query(models_project.Project).filter(models_project.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
    return db_project

@router.put("/projects/{project_id}", response_model=schemas.ProjectResponse)
def update_project(project_id: int, project_data: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    """Actualiza la información de un proyecto existente."""
    db_project = db.query(models_project.Project).filter(models_project.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")

    update_dict = project_data.model_dump(exclude_unset=True)
    if "name" in update_dict and update_dict["name"] != db_project.name:
        dup = db.query(models_project.Project).filter(models_project.Project.name == update_dict["name"]).first()
        if dup:
            raise HTTPException(status_code=409, detail=f"Ya existe otro proyecto con el nombre '{update_dict['name']}'.")

    for key, value in update_dict.items():
        setattr(db_project, key, value)

    try:
        db.commit()
        db.refresh(db_project)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Error de integridad al actualizar el proyecto.")
    return db_project

@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Elimina un proyecto únicamente si no tiene datos asociados."""
    db_project = db.query(models_project.Project).filter(models_project.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")

    # Verificar si existen casos, suites, conexiones o historial dependientes
    if len(db_project.test_cases) > 0 or len(db_project.test_suites) > 0 or len(db_project.connection_profiles) > 0:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar el proyecto porque contiene casos, suites o perfiles de conexión asociados."
        )
    if hasattr(db_project, 'execution_histories') and len(db_project.execution_histories) > 0:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar el proyecto porque conserva historial de ejecuciones."
        )

    try:
        db.delete(db_project)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Error de integridad: el proyecto tiene dependencias que impiden su eliminación.")
    return
