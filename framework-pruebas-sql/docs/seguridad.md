# Seguridad

## Autenticación y Acceso
El sistema implementa protección mediante sesión por Cookie (`HttpOnly`, `SameSite=Lax`).
- Se requiere definir `APP_ACCESS_ENABLED=true` en `.env`.
- Definir credenciales de entorno: `APP_ACCESS_USERNAME` y `APP_ACCESS_PASSWORD`.
- Definir el secreto de sesión en `APP_SESSION_SECRET` para firmar la cookie.
- Las contraseñas de Oracle se solicitan explícitamente durante el runtime y nunca se guardan en `framework_interno.db` ni en el navegador.

## Motor de Políticas SQL (`sql_policy.py`)
El motor de validación se divide en 3 anillos de seguridad implementados con `sqlparse`:

1. **Bloqueo Global (DDL y TCL):** Rechaza de forma determinista instrucciones como `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `COMMIT`, `ROLLBACK` y PL/SQL (`BEGIN`, `DECLARE`, `EXECUTE`) para impedir la destrucción no deseada de metadatos o fugas transaccionales.
2. **Sentencias Múltiples:** Se bloquean inyecciones de múltiples consultas separadas por punto y coma `;` en todos los entornos.
3. **Control por Ambiente (`environment_type`):**
   - **`TEST`:** Permite operaciones `SELECT`, `INSERT`, `UPDATE` y `DELETE`. Cualquier sentencia DML es automáticamente encapsulada en una transacción estricta que aborta con un `ROLLBACK` obligatorio.
   - **`STAGING`:** Permite las mismas operaciones que `TEST` (con `ROLLBACK` obligatorio), pero exige **confirmación explícita desde el backend** para ejecutar cualquier operación DML; de lo contrario es rechazada.
   - **`PRODUCTION`:** Bloquea **toda sentencia DML a nivel de API backend** (independientemente del cliente). Solo permite la ejecución de sentencias `SELECT`. Además, los resultados de datos reales se enmascaran en los historiales de ejecución (`ExecutionHistory`), mostrando únicamente el número de filas operadas. Los mensajes de error originales provenientes del driver de base de datos también se enmascaran para evitar filtraciones de nombres de tablas o literales en constraints.

   > **IMPORTANTE PARA PRODUCCIÓN:** El analizador SQL del backend es una capa de defensa en profundidad, pero **no garantiza seguridad total por sí solo**. Para uso real en producción, el perfil de conexión debe configurarse obligatoriamente con un **usuario Oracle exclusivo que tenga únicamente permisos de lectura (SELECT)** sobre las tablas necesarias. Nunca utilice usuarios con permisos de escritura, DDL o roles de administrador (DBA) para los perfiles de producción.

   *Advertencia para Evaluadores*: El `executed_sql` y el `expected_result` persisten exactamente como fueron redactados en el caso de prueba. No se deben incluir PII ni datos sensibles directamente en las sentencias SQL de los tests.

## Restricción de Recursos
A fin de proteger los entornos de pruebas y producción frente a sobrecargas y errores de sintaxis que produzcan bucles, se aplican dos variables de entorno obligatorias que restringen los recursos:
- `MAX_RESULT_ROWS` (default: 1000): Protege al backend de cuellos de botella truncando las listas de datos devueltas por los comandos `SELECT`.
- `ORACLE_CALL_TIMEOUT_MS` (default: 10000 ms): Aplica un tiempo máximo de retardo por llamada para la conexión con el driver Oracle, cortando conexiones congeladas.
