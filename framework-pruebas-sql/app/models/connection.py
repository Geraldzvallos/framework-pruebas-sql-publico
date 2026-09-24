"""
Modelo de base de datos para Perfiles de Conexión Oracle (sin columna de contraseña).
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class ConnectionProfile(Base):
    __tablename__ = "connection_profiles"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    engine = Column(String, default="ORACLE", nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, default=1521, nullable=False)
    service_name = Column(String, nullable=False)
    username = Column(String, nullable=False)
    environment_type = Column(String, default="TEST", nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    project = relationship("Project", back_populates="connection_profiles")
    execution_histories = relationship("ExecutionHistory", back_populates="connection_profile")
