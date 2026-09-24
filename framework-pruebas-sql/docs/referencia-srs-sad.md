# Referencia SRS y SAD (Software Requirements & Architecture Document)

## 1. Objetivo y Alcance Implementado
El **Framework de Pruebas de Base de Datos SQL** es un entorno diseñado para evaluar, gestionar y automatizar la ejecución de sentencias SQL (específicamente DML: INSERT, UPDATE, DELETE) contra una base de datos Oracle, aplicando validaciones de resultados (ROW_COUNT, EXISTS) de forma segura y garantizando que toda operación modificadora desencadene un ROLLBACK.

## 2. Actores Reales
- **Tester / Analista QA**: Usuario principal, encargado de configurar los perfiles de conexión, redactar los casos de prueba y ejecutar las suites.
- **Administrador**: Puede gestionar la infraestructura general y credenciales de acceso global (`APP_ACCESS_USERNAME` y `APP_ACCESS_PASSWORD`).

## 3. Módulos Funcionales
1. **Gestión de Proyectos**: Agrupador lógico superior para conexiones y pruebas.
2. **Perfiles de Conexión**: Repositorio temporal (sin almacenar contraseñas) de parámetros de conexión a bases de datos Oracle.
3. **Casos de Prueba**: Definiciones individuales de consultas SQL y resultados esperados.
4. **Suites de Pruebas**: Colección ordenada de casos ejecutables en ráfaga.
5. **Historial de Ejecuciones**: Trazabilidad completa con resultados PASS/FAIL/ERROR y métricas de rendimiento.

## 4. Requisitos Funcionales y Trazabilidad

| Requisito | Módulo | Endpoint/Función | Prueba | Estado |
|---|---|---|---|---|
| Autenticación Global | Seguridad (`api.js`) | Middleware (Cookie HttpOnly) | `tests/test_auth.py` | Implementado |
| CRUD Proyectos | Proyectos (`proyectos.js`) | `/api/projects/` | `tests/test_core_models.py` | Implementado |
| CRUD Conexiones | Conexiones (`conexiones.js`) | `/api/connections/` | `tests/test_core_models.py` | Implementado |
| Probar Conexión | Conexiones (`conexiones.js`) | `/api/connections/{id}/test` | `tests/test_engine.py` | Implementado |
| CRUD Casos | Casos (`casos.js`) | `/api/test-cases/` | `tests/test_core_models.py` | Implementado |
| CRUD Suites | Suites (`suites.js`) | `/api/suites/` | `tests/test_core_models.py` | Implementado |
| Ejecutar Caso DML | Motor SQL (`ejecutor.js`) | `/api/execute/test-case/{id}` | `tests/test_execution_engine.py` | Implementado |
| Ejecutar Suite | Motor SQL (`ejecutor.js`) | `/api/execute/suite/{id}` | `tests/test_execution_engine.py` | Implementado |
| Rollback Obligatorio | Motor SQL (`ejecutor.js`) | `app/engine/executor.py` | `tests/test_execution_engine.py` | Implementado |
| Registro Historial | Historial (`historial.js`) | `/api/history/` | `tests/test_history_pagination.py` | Implementado |
| Políticas por Ambiente | Motor SQL (`sql_policy.py`) | `app/security/sql_policy.py` | `tests/test_environment_policies.py` | Implementado |

## 5. Arquitectura Lógica y Física
- **Frontend**: Single Page Application nativa (HTML, CSS, JS Modular).
- **Backend**: API RESTful en Python (FastAPI, Pydantic v2).
- **Persistencia Interna**: SQLite gestionado por SQLAlchemy y Alembic (esquema inmutable durante pruebas gracias a `:memory:` con `StaticPool`).
- **Persistencia Objetivo**: Oracle DB.

## 6. Decisiones Técnicas y Limitaciones Actuales
- Las contraseñas de las conexiones Oracle nunca se persisten en base de datos; se solicitan en tiempo de ejecución para cada ejecución DML o prueba de conectividad.
- El despliegue se ha preparado mediante Docker y Docker Compose (`infra/production/compose.yml`), asegurando persistencia mediante volúmenes de Docker, aunque el despliegue a producción cloud se encuentra marcado como pendiente de DNS y secretos finales de CI/CD.
- Para evitar efectos secundarios en el repositorio local durante las pruebas automáticas con Pytest, se utiliza una base de datos SQLite en memoria (`:memory:`).
- Se cuenta con automatización CI/CD limitada intencionalmente (deploy truncado) hasta proveer infraestructura productiva.

## 7. Políticas de Seguridad por Ambiente
- **TEST:** Permite la ejecución de sentencias DML (INSERT, UPDATE, DELETE) encapsuladas en una transacción estricta con ROLLBACK automático obligatorio.
- **STAGING:** Permite la ejecución de DML con ROLLBACK obligatorio, pero requiere explícitamente confirmación de la capa cliente (y validación del backend) antes de su ejecución.
- **PRODUCTION:** Bloquea estrictamente cualquier intento de ejecución de sentencias DML desde el backend (independiente del cliente). Solo permite sentencias de solo lectura (`SELECT`). Adicionalmente se enmascaran resultados para no exponer datos reales y se exige configuración de un usuario Oracle con permisos exclusivos de solo lectura.
