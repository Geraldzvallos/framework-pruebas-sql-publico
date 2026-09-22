"""
Endpoints REST para la gestión de Perfiles de Conexión Oracle (sin persistencia de contraseñas).
"""
import oracledb
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import connection as models_conn
from app.models import project as models_project
from app.models import schemas
from app.engine.executor import TargetDatabaseExecutor

router = APIRouter()

@router.post("/connections/", response_model=schemas.ConnectionProfileResponse, status_code=201)
def create_connection_profile(profile: schemas.ConnectionProfileCreate, db: Session = Depends(get_db)):
    """Crea un nuevo perfil de conexión Oracle para un proyecto (sin contraseña)."""
    project = db.query(models_project.Project).filter(models_project.Project.id == profile.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Proyecto ID {profile.project_id} no encontrado.")

    db_profile = models_conn.ConnectionProfile(**profile.model_dump())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@router.get("/connections/", response_model=list[schemas.ConnectionProfileResponse])
def get_connection_profiles(
    project_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obtiene la lista de perfiles de conexión filtrados opcionalmente por proyecto."""
    query = db.query(models_conn.ConnectionProfile)
    if project_id:
        query = query.filter(models_conn.ConnectionProfile.project_id == project_id)
    profiles = query.offset(skip).limit(limit).all()
    return profiles

@router.get("/connections/{connection_id}", response_model=schemas.ConnectionProfileResponse)
def get_connection_profile(connection_id: int, db: Session = Depends(get_db)):
    """Obtiene un perfil de conexión por su ID."""
    profile = db.query(models_conn.ConnectionProfile).filter(models_conn.ConnectionProfile.id == connection_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil de conexión no encontrado.")
    return profile

@router.put("/connections/{connection_id}", response_model=schemas.ConnectionProfileResponse)
def update_connection_profile(connection_id: int, profile_data: schemas.ConnectionProfileUpdate, db: Session = Depends(get_db)):
    """Actualiza la información de un perfil de conexión."""
    profile = db.query(models_conn.ConnectionProfile).filter(models_conn.ConnectionProfile.id == connection_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil de conexión no encontrado.")

    update_dict = profile_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile

@router.delete("/connections/{connection_id}", status_code=204)
def delete_connection_profile(connection_id: int, db: Session = Depends(get_db)):
    """Elimina un perfil de conexión."""
    profile = db.query(models_conn.ConnectionProfile).filter(models_conn.ConnectionProfile.id == connection_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil de conexión no encontrado.")

    db.delete(profile)
    db.commit()
    return

@router.post("/connections/{connection_id}/test", response_model=schemas.ExecutionResponse)
def test_connection_profile(
    connection_id: int,
    request: schemas.TestConnectionRequest,
    db: Session = Depends(get_db)
):
    """
    Prueba la conectividad de un perfil Oracle usando la contraseña enviada en el cuerpo.
    Construye el DSN con oracledb.makedsn y descarta la contraseña de inmediato.
    """
    profile = db.query(models_conn.ConnectionProfile).filter(models_conn.ConnectionProfile.id == connection_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil de conexión no encontrado.")

    try:
        dsn = oracledb.makedsn(profile.host, profile.port, service_name=profile.service_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al construir el DSN: {str(e)}")

    executor = TargetDatabaseExecutor(dsn=dsn, user=profile.username, password=request.password)
    try:
        res = executor.execute_query("SELECT 1 FROM DUAL")
        if not res["success"]:
            raise HTTPException(status_code=400, detail=res.get("error_message") or res.get("message"))
        return schemas.ExecutionResponse(
            success=True,
            statement_type="SELECT",
            rows=res["rows"],
            rowcount=res["rowcount"],
            data=res["rows"],
            message=f"Conexión exitosa al perfil '{profile.name}' en Oracle.",
            error_message=None
        )
    finally:
        executor.disconnect()
