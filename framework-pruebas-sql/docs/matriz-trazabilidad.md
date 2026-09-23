# Matriz de Trazabilidad

| ID Requisito | Funcionalidad | Componente Backend | Componente Frontend | Pruebas Automatizadas |
|--------------|---------------|--------------------|---------------------|-----------------------|
| REQ-01 | Gestión de Proyectos | `/api/projects/` | `js/modulos/proyectos.js` | `test_core_models.py` |
| REQ-02 | Gestión de Conexiones | `/api/connections/` | `js/modulos/conexiones.js` | `test_core_models.py` |
| REQ-03 | Gestión de Casos de Prueba | `/api/test-cases/` | `js/modulos/casos.js` | `test_core_models.py` |
| REQ-04 | Agrupación de Suites | `/api/suites/` | `js/modulos/suites.js` | `test_core_models.py` |
| REQ-05 | Ejecución Oracle y Rollback | `app/services/execution_service.py`, `app/engine/executor.py` | `js/modulos/ejecutor.js` | `test_execution_engine.py`, `test_oracle_integration.py` |
| REQ-06 | Paginación y Filtrado Historial| `/api/history/` | `js/modulos/historial.js` | `test_history_pagination.py` |
| REQ-07 | Seguridad de Autenticación | Middleware (FastAPI) | `js/core/api.js` | `test_auth.py` |
| REQ-08 | Dashboard de KPIs | `/api/history/` | `js/modulos/dashboard.js` | `test_revision_final_frontend.py` |
