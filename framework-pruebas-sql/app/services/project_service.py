"""
Servicio para inicializar y gestionar proyectos en la base de datos interna.
"""
from sqlalchemy.orm import Session
from app.models.project import Project


def ensure_default_project(db: Session) -> Project:
    """Garantiza la existencia del 'Proyecto general' inicial."""
    project = db.query(Project).filter(Project.id == 1).first()
    if not project:
        project = Project(
            id=1,
            name="Proyecto general",
            description="Proyecto creado automáticamente por el framework para asignación inicial."
        )
        db.add(project)
        db.commit()
        db.refresh(project)
    return project
