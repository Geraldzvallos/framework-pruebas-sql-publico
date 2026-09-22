# Manual Técnico

## Pila Tecnológica
- **Backend**: Python 3.12+, FastAPI, Uvicorn, SQLAlchemy.
- **Base de Datos Interna**: SQLite (`framework_interno.db`) orquestada mediante Alembic.
- **Motor Objetivo**: Oracle Database Free (`oracledb` Thin Driver).
- **Frontend**: Vanilla JS, HTML, CSS y Bootstrap 5 (sin frameworks reactivos).
- **Pruebas**: Pytest (entorno aislado en memoria para SQLite).

## Estructura del Código
- `app/api/`: Controladores REST.
- `app/core/`: Configuración y conexión SQLite.
- `app/engine/`: Módulo crítico de validación y ejecución SQL (`TargetDatabaseExecutor` y `ValidationStrategy`).
- `app/models/`: Entidades de dominio Pydantic y SQLAlchemy.
- `app/services/`: Capa de servicios que orquesta las llamadas al motor.

## Aislamiento de Ejecución
La clase `TargetDatabaseExecutor` es responsable de:
1. Conectar a Oracle con `autocommit=False`.
2. Ejecutar la instrucción.
3. Evaluar el estado.
4. Invocar `connection.rollback()` incondicionalmente tras DML.

## Seguridad de Acceso
En entornos productivos (`APP_ACCESS_ENABLED=true`), se activa el middleware HTTP Basic Auth configurado en `app/main.py`. Este valida mediante comparación segura (`secrets.compare_digest`) las credenciales proporcionadas con las inyectadas en las variables de entorno (`APP_ACCESS_USERNAME` y `APP_ACCESS_PASSWORD`).
