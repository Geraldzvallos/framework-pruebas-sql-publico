import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import Engine

# URL de nuestra base de datos interna local (SQLite o la especificada en FRAMEWORK_DB_URL)
SQLALCHEMY_DATABASE_URL = os.getenv("FRAMEWORK_DB_URL", "sqlite:///./framework_interno.db")

# Creamos el motor de conexión
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Habilitar pragma de claves foráneas en SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Creamos la fábrica de sesiones para interactuar con la BD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base de la que heredarán todos nuestros modelos (tablas)
Base = declarative_base()

# Inyección de dependencias para la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 