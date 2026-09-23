# Matriz de Trazabilidad

| ID Requisito | Funcionalidad | Componente Backend | Componente Frontend | Pruebas Automatizadas |
|--------------|---------------|--------------------|---------------------|-----------------------|
| REQ-01 | Gestión de Proyectos | `app.api.projects` | `js/modulos/proyectos.js` | `test_api_endpoints.py` |
| REQ-02 | Gestión de Conexiones | `app.api.connections` | `js/modulos/conexiones.js` | `test_api_endpoints.py` |
| REQ-03 | Gestión de Casos de Prueba | `app.api.test_cases` | `js/modulos/casos.js` | `test_core_models.py`, `test_api_endpoints.py` |
| REQ-04 | Agrupación de Suites | `app.api.suites` | `js/modulos/suites.js` | `test_api_endpoints.py` |
| REQ-05 | Ejecución Oracle y Rollback | `app.api.executions` | `js/modulos/ejecutor.js` | `test_execution_engine.py`, `test_oracle_integration.py` |
| REQ-06 | Paginación y Filtrado Historial| `app.api.history` | `js/modulos/historial.js` | `test_history_pagination.py` |
| REQ-07 | Seguridad de Autenticación | `app.main.basic_auth_middleware`| (A través de `.env`) | `test_auth.py` |
| REQ-08 | Dashboard de KPIs | `app.api.history` | `js/modulos/dashboard.js` | `test_revision_final_frontend.py` |
