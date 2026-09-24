# Seguridad

## Autenticación y Acceso
El sistema implementa protección mediante Middleware `basic_auth_middleware`.
- Se requiere definir `APP_ACCESS_ENABLED=true` en `.env`.
- Definir credenciales de entorno: `APP_ACCESS_USERNAME` y `APP_ACCESS_PASSWORD`.
- Las contraseñas de Oracle se solicitan explícitamente durante el runtime y nunca se guardan en `framework_interno.db`.

## Motor de Políticas SQL (`sql_policy.py`)
El motor de validación se divide en 3 anillos de seguridad implementados con `sqlparse`:

1. **Bloqueo Global (DDL y TCL):** Rechaza de forma determinista instrucciones como `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `COMMIT`, `ROLLBACK` y PL/SQL (`BEGIN`, `DECLARE`, `EXECUTE`) para impedir la destrucción no deseada de metadatos o fugas transaccionales.
2. **Sentencias Múltiples:** Se bloquean inyecciones de múltiples consultas separadas por punto y coma `;` en todos los entornos.
3. **Control por Ambiente (`environment_type`):**
   - **`TEST` y `STAGING`:** Permiten operaciones `SELECT`, `INSERT`, `UPDATE` y `DELETE`. Cualquier sentencia DML es automáticamente encapsulada en una transacción estricta que aborta con un `ROLLBACK` obligatorio, el cual es validado por el backend para evitar datos sucios.
   - **`PRODUCTION`:** Bloquea **toda sentencia DML a nivel de API backend** (independientemente del cliente). Solo permite la ejecución de sentencias `SELECT`. Además, los resultados de datos reales se enmascaran en los historiales de ejecución (`ExecutionHistory`), mostrando únicamente el número de filas operadas.

## Restricción de Recursos
A fin de proteger los entornos de pruebas y producción frente a sobrecargas y errores de sintaxis que produzcan bucles, se aplican dos variables de entorno obligatorias que restringen los recursos:
- `MAX_RESULT_ROWS` (default: 1000): Protege al backend de cuellos de botella truncando las listas de datos devueltas por los comandos `SELECT`.
- `ORACLE_CALL_TIMEOUT_MS` (default: 10000 ms): Aplica un tiempo máximo de retardo por llamada para la conexión con el driver Oracle, cortando conexiones congeladas.
