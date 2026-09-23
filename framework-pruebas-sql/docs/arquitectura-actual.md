# Arquitectura Actual del Framework de Pruebas SQL

## Componentes Reales
El proyecto sigue una arquitectura cliente-servidor, con un frontend monolítico, una API RESTful en el backend y persistencia dual en bases de datos SQLite y Oracle.

### 1. Frontend
Actualmente monolítico.
- **`frontend/index.html`**: Estructura principal, estilos y diseño (Bootstrap 5, SweetAlert2).
- **`frontend/app.js`**: Toda la lógica de cliente, interacciones DOM, llamadas HTTP y estado global (36KB).

### 2. Backend (API REST)
Desarrollado en Python con FastAPI.
- **`app/main.py`**: Punto de entrada de la aplicación y configuración de CORS.
- **`app/api/`**: Controladores de los endpoints.
- **`app/core/`**: Configuraciones generales y seguridad.
- **`app/engine/`**: Ejecución de las sentencias SQL (Oracle y SQLite).
- **`app/models/`**: Modelos ORM (SQLAlchemy) y esquemas Pydantic.
- **`app/services/`**: Lógica de negocio de la aplicación.

### 3. Persistencia de Datos
- **SQLite (`framework_interno.db`)**: Base de datos interna administrada por SQLAlchemy y Alembic para el control de proyectos, perfiles de conexión, casos de prueba, suites e historial de ejecuciones.
- **Oracle DB**: Base de datos sometida a las pruebas del QA Framework a través del módulo `cx_Oracle` / `oracledb`.

### 4. Infraestructura (Docker)
- **`Dockerfile`**: Definición de la imagen para el backend y frontend (servido por FastAPI).
- **`infra/production/compose.yml`**: Define los servicios `api` y `oracle_db`.
- **`infra/oracle/init/`**: Scripts de inicialización de la base de datos Oracle para pruebas.

## Flujo de Datos
1. El usuario interactúa con la UI (SPA en `index.html` + `app.js`).
2. El frontend consume la API REST.
3. La API (FastAPI) registra/recupera información de metadatos en **SQLite**.
4. Cuando se ejecutan pruebas DML, la API se conecta a **Oracle DB** usando los perfiles de conexión, ejecuta la consulta, realiza el ROLLBACK obligatorio si corresponde y retorna el resultado (PASS/FAIL/ERROR) para ser persistido en SQLite.

## Endpoints Principales
- `/projects/`: Gestión de proyectos.
- `/connections/`: Gestión de perfiles de conexión.
- `/test-cases/`: Gestión de casos de prueba DML y SELECT.
- `/suites/`: Agrupación de casos.
- `/execute/`: Ejecución contra la base de datos objetivo.
- `/history/`: Historial y trazabilidad de ejecuciones.

## Variables de Entorno Utilizadas
- `API_HOST`, `API_PORT`: Configuración del servidor.
- `APP_ACCESS_ENABLED`, `APP_ACCESS_USERNAME`, `APP_ACCESS_PASSWORD`: Credenciales globales de acceso.
- `CORS_ORIGINS`: Restricciones CORS.
- `FRAMEWORK_DB_URL`: URL de conexión a la base interna SQLite.
- `RUN_ORACLE_TESTS`: Bandera para habilitar las pruebas de integración Oracle.
- Variables Oracle: `FRAMEWORK_TEST_PASSWORD`, `ORACLE_PWD`.

## Pruebas
- Pruebas unitarias de la API utilizando `pytest`.
- Pruebas de integración con Oracle (marcadas con `oracle_integration`).
- Validaciones en CI configuradas con GitHub Actions.
