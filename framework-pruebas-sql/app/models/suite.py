"""
Modelo de base de datos para las Suites de Pruebas.
Permite agrupar múltiples Casos de Prueba para su ejecución en bloque.
"""
from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

suite_test_case_table = Table(
    "suite_test_case",
    Base.metadata,
    Column("suite_id", Integer, ForeignKey("test_suites.id"), primary_key=True),
    Column("test_case_id", Integer, ForeignKey("test_cases.id"), primary_key=True)
)

class TestSuite(Base):
    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, default=1)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)

    project = relationship("Project", back_populates="test_suites")
    test_cases = relationship("TestCase", secondary=suite_test_case_table, backref="suites")
    execution_histories = relationship("ExecutionHistory", back_populates="test_suite")