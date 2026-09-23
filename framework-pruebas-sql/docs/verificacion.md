# Verificación

## Testing Local (Pytest)
El proyecto contiene pruebas que aseguran la correcta integración de todos los componentes.
Ejecución normal sin necesidad de Oracle DB local (utiliza una SQLite temporal in-memory aislada):
```bash
pytest -q -m "not oracle_integration"
```

Ejecución de pruebas con Oracle (Requiere `RUN_ORACLE_TESTS=1` y `FRAMEWORK_TEST_PASSWORD`):
```bash
pytest -q -m oracle_integration
```

## Validación Frontend y Sintaxis
Las pruebas automáticas `test_revision_final_frontend.py` validan que la arquitectura modular `app.js` interactúe correctamente sin fugas.
