"""
Modelo de base de datos para Casos de Prueba SQL.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, default=1)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    sql_query = Column(Text, nullable=False)
    expected_result = Column(String, nullable=False)
    validation_type = Column(String, nullable=False, default="ROW_COUNT")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="test_cases")
    execution_histories = relationship("ExecutionHistory", back_populates="test_case")