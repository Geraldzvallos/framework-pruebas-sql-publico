"""
Configuración de aislamiento de base de datos para Pytest.
Utiliza SQLite en memoria (:memory:) para garantizar que la base de datos
interna local (framework_interno.db) nunca sea modificada durante las pruebas.
"""
import os

# Configurar variable de entorno para la base de datos de pruebas en memoria ANTES de las importaciones
os.environ["FRAMEWORK_DB_URL"] = "sqlite:///:memory:"

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.main import app

# Retener la variable test_engine antigua sólo por compatibilidad global si algún test lo importa directamente
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(autouse=True, scope="function")
def setup_isolated_db():
    """
    Crea una base de datos temporal en memoria COMPLETAMENTE NUEVA para cada prueba.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma_test(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[get_db] = override_get_db
    
    # Update the global TestingSessionLocal and test_engine for tests that import them directly
    global TestingSessionLocal, test_engine
    test_engine = engine
    TestingSessionLocal = TestingSession
    
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
