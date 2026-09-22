# Framework de Pruebas de Base de Datos SQL

## 1. Nombre Oficial
**Framework de pruebas de base de datos SQL**

## 2. Objetivo
El objetivo del sistema es permitir definir, ejecutar, validar y registrar pruebas automáticas sobre bases de datos SQL relacionales (con Oracle como motor objetivo para el MVP), garantizando el aislamiento transaccional mediante el uso obligatorio de `ROLLBACK` y la trazabilidad de la evidencia de ejecución.

## 3. Tecnologías
- **Lenguaje:** Python 3.x
- **API Web:** FastAPI + Uvicorn
- **ORM y Persistencia Interna:** SQLAlchemy + SQLite (`framework_interno.db`)
- **Conector Objetivo:** `oracledb` (Modo Thin)
- **Analizador SQL:** `sqlparse`
- **Pruebas y Mocks:** Pytest + FastAPI TestClient (`httpx2`)
- **Frontend:** Vanilla HTML, CSS (Bootstrap 5) y JavaScript

## 4. Arquitectura Actual
El sistema sigue una arquitectura modular y desacoplada por capas:
- **Frontend**: Interfaz web completa e integrada en `/ui/`. Incluye paneles de proyectos, conexiones, casos de prueba, ejecución de suites e historial con soporte móvil.
- **API (Controladores / Routers)**: Endpoints REST v2 (`/projects`, `/connections`, `/test-cases`, `/suites`, `/history`, `/execute`).
- **Core & Persistencia**: Gestión de sesión y contexto de base de datos SQLite interna (`framework_interno.db`) con soporte de claves foráneas `PRAGMA foreign_keys = ON;` y migraciones con **Alembic**.
- **Services (Capa de Servicios Centralizada)**:
  - `ExecutionService`: Orquestación centralizada de ejecuciones (individuales y por suite), selección de estrategia de validación (`ROW_COUNT` y `EXISTS`), formateo seguro de evidencias y registro en historial.
  - `ProjectService`: Inicialización transparente del proyecto predeterminado ("Proyecto general", ID=1).
- **Engine (Motor SQL y Validación)**:
  - `TargetDatabaseExecutor`: Administración de conexiones Oracle (o simuladas en pruebas), validación estricta de sentencias (bloqueo de DDL/comandos peligrosos y múltiples sentencias) y aplicación de `ROLLBACK` obligatorio.
  - `ValidationContext` / `RowCountValidation` / `ExistenceValidation`: Patrón Strategy para la comparación de resultados esperados vs. obtenidos.
- **Models**: Esquemas Pydantic v2 con validación estricta de tipos de datos y modelos ORM de SQLAlchemy.

## 5. Requisitos de Sistema
- Python 3.10 o superior
- Pip (Administrador de paquetes de Python)
- Git

## 6. Creación del Entorno Virtual
```bash
# Crear el entorno virtual
python -m venv venv

# Activar el entorno virtual (Linux/macOS)
source venv/bin/activate

# Activar el entorno virtual (Windows PowerShell)
.\venv\Scripts\Activate.ps1
```

## 7. Instalación de Dependencias y Migraciones
```bash
pip install -r requirements.txt

# Aplicar migraciones de la base de datos interna SQLite
alembic upgrade head
```

## 8. Ejecución del Backend
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
La documentación interactiva estará disponible en: `http://127.0.0.1:8000/docs`

## 9. Ejecución del Frontend
El frontend se sirve desde la misma aplicación FastAPI. Después de iniciar Uvicorn, abre:

```text
http://127.0.0.1:8000/ui/
```

No abras `frontend/index.html` mediante `file://`, porque el flujo oficial utiliza el mismo origen del backend y la ruta relativa `/api`.

## 10. Ejecución de Pruebas Automáticas (Pytest)
```bash
pytest -v
```
*Nota: Las pruebas automáticas corren sobre una base de datos SQLite en memoria aislada (`:memory:`) sin alterar `framework_interno.db` ni requerir una conexión Oracle real.*
El total de pruebas de la suite completa se informa en los resultados de cada fase. Oracle Database Free ya fue validado localmente en la Fase 4.1.1 (con 60 pruebas normales y 11 pruebas Oracle separadas). La contraseña se solicita únicamente al probar o ejecutar y nunca se persiste. El producto no debe utilizarse contra una base Oracle de producción.

## 11. Uso del Archivo `.env.example`
Copia la plantilla de variables de entorno y ajusta los valores locales si es necesario:
```bash
cp .env.example .env
```
Contenido de muestra:
- `FRAMEWORK_DB_URL`: Ruta o URL de la base de datos interna.
- `CORS_ORIGINS`: Lista de orígenes web permitidos.

Los datos del perfil Oracle se registran desde la interfaz. La contraseña se solicita únicamente al probar o ejecutar y no se guarda en `.env` ni en SQLite.

## 12. Funcionalidades Implementadas (Fase 1 y Fase 2)
- [x] **Gestión de Proyectos (CRUD):** Creación, lectura, actualización y eliminación de proyectos. Prevención de eliminación si existen dependencias.
- [x] **Perfiles de Conexión (CRUD sin contraseñas):** Configuración de hosts, puertos, usernames y service names. Las contraseñas NO se almacenan en SQLite (ni en texto plano ni cifradas).
- [x] **Prueba de Conexión:** Endpoint `/connections/{id}/test` para validar credenciales sin guardar la contraseña.
- [x] **Casos de Prueba con validation_type:** Soporte para estancias de validación por `ROW_COUNT` (número de filas afectadas) y `EXISTS` (verificación boolean true/false).
- [x] **Suites de Pruebas:** Agrupación de casos pertenecientes al mismo proyecto con validaciones de integridad (mismo proyecto, sin duplicados).
- [x] **Motor de Ejecución Centalizado:** Motor SQL robusto con `ROLLBACK` obligatorio tras DML, enmascaramiento de secretos y captura de evidencia.
- [x] **Historial Completo y Trazabilidad:** Registro persistente de ejecuciones (`ExecutionHistory`) incluyendo `project_id`, `suite_id`, `connection_profile_id`, `statement_type`, `validation_type`, `expected_result`, `actual_result`, `rowcount`, `rollback_applied` y `error_message`.
- [x] **Consultas con Filtros y Paginación:** Búsqueda en historial por `project_id`, `test_case_id`, `suite_id` y `status`.
- [x] **Migraciones Alembic:** Control de versiones de esquema de base de datos SQLite con soporte para SQLite batch mode (`render_as_batch=True`).
- [x] **Aislamiento Total en Pruebas:** Pytest 100% aislado en memoria (`:memory:`), sin modificar `framework_interno.db`.

## 13. Funcionalidades Pendientes (Fases Futuras)
- [x] Validación Oracle Real (Fase 4): Ejecución comprobada contra una base de datos Oracle XE o similar en un contenedor Docker.
- [x] Preparación de producción y despliegue (Fase 4.2): variables, almacenamiento persistente, acceso protegido y pruebas sobre la URL publicada (despliegue público en curso).

## 14. Advertencia de Seguridad
> [!CAUTION]
> **NO UTILIZAR UNA BASE DE DATOS ORACLE DE PRODUCCIÓN.**
> Ejecute el framework únicamente contra entornos de pruebas de bases de datos dedicados o aislados. Aunque el framework aplica `ROLLBACK` de forma obligatoria en operaciones DML, nunca debe probarse contra entornos de producción reales.

## 15. Explicación del Mecanismo de Rollback
Las pruebas que modifican datos (`INSERT`, `UPDATE`, `DELETE`) deben ejecutarse sin dejar datos residuales en la base de datos objetivo.
El flujo de ejecución es:
1. Se abre la conexión y se desactiva `autocommit` (`autocommit = False`).
2. Se ejecuta la sentencia DML dentro de la transacción.
3. Se captura el número de filas afectadas (`cursor.rowcount`).
4. Se ejecuta de forma inmediata y obligatoria `connection.rollback()`.
5. Se verifica si el `rollback` fue aplicado exitosamente (`rollback_applied = True`).
6. Si el `rollback` falla, la prueba es marcada automáticamente como `FAIL/ERROR` (`success = False`).
7. **Nunca se ejecuta `COMMIT`.**

## 16. Estructura del Proyecto
```text
framework_pruebas_sql/
├── alembic/             # Control de versiones de esquemas de BD (Alembic)
├── app/
│   ├── api/             # Endpoints y controladores REST (FastAPI)
│   ├── core/            # Base de datos y configuración SQLite
│   ├── engine/          # Motor SQL (Executor) y Estrategias de Validación
│   ├── models/          # Modelos ORM SQLAlchemy y Esquemas Pydantic
│   └── services/        # Capa de Servicios (Orquestador de ejecuciones)
├── frontend/            # Interfaz de usuario (HTML, CSS, JS)
├── infra/               # Infraestructura y contenedores Docker (Oracle local)
├── tests/               # Pruebas automáticas (Pytest + Mocks + TestClient)
├── alembic.ini          # Configuración de Alembic
├── framework_interno.db # Base de datos SQLite interna (desarrollo)
├── pytest.ini           # Configuración de Pytest
├── README.md            # Documentación del proyecto
└── requirements.txt     # Lista de dependencias de Python
```

## 17. Oracle Database Free para Pruebas Locales (Fase 4.1)

Para realizar pruebas DML completas con `ROLLBACK` contra un motor real, el proyecto ahora incluye configuración para Oracle Database Free mediante Docker.

### Requisitos
- Docker y Docker Compose
- Recursos suficientes (el contenedor de Oracle requiere aproximadamente 2GB de RAM)

### Configuración
1. Copie el archivo `.env.oracle.example` a `.env.oracle`.
2. Modifique las variables estableciendo contraseñas seguras para `ORACLE_PWD` y `FRAMEWORK_TEST_PASSWORD`.
3. Inicie Oracle localmente desde el directorio `infra/oracle`.
4. Espere el estado `healthy` del contenedor.
5. Establezca la variable de entorno `RUN_ORACLE_TESTS=1` solo para ejecutar integración real.
6. Ejecute por separado las pruebas normales y pruebas Oracle.
7. ¡Precaución! No comparta, no envíe al control de versiones ni comprima nunca su archivo `.env.oracle`.

### Comandos de Inicialización
```bash
# Iniciar la base de datos y esperar la inicialización
cd infra/oracle
docker compose up -d

# Ver los logs para confirmar que está lista ("DATABASE IS READY TO USE")
docker compose logs -f
```

El script de inicialización (`001_test_schema.sh`) crea automáticamente un usuario exclusivo llamado `FRAMEWORK_TEST` con permisos mínimos, y una tabla de ejemplo `FRAMEWORK_TEST_ITEMS` necesaria para la suite de integración.

### Solución de Errores Comunes
- **ORA-01017 (Invalid credential)**: Verifique que `.env.oracle` contiene `ORACLE_PWD` en lugar de `ORACLE_PASSWORD`, de acuerdo al estándar de la imagen oficial de Oracle.
- **Contenedor lento al iniciar**: Oracle Free toma de 1 a 3 minutos en iniciar los esquemas conectables (`FREEPDB1`). Utilice `docker ps` para ver si el estado cambió a `healthy`.

### Ejecutar las Pruebas de Integración Reales
Asegúrese de que el entorno contenga las variables del archivo `.env.oracle` (puede exportarlas o usar utilidades como `python-dotenv`). Las pruebas saltarán automáticamente si las credenciales de Oracle no están presentes.
```bash
pytest -v -m oracle_integration
```
