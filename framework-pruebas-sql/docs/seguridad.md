# Seguridad

## Autenticación y Acceso
El sistema implementa protección mediante Middleware `basic_auth_middleware`.
- Se requiere definir `APP_ACCESS_ENABLED=true` en `.env`.
- Definir credenciales de entorno: `APP_ACCESS_USERNAME` y `APP_ACCESS_PASSWORD`.
- Las contraseñas de Oracle se solicitan explícitamente durante el runtime y nunca se guardan en `framework_interno.db`.

## Bloqueo de DDL
El motor rechaza de forma determinista instrucciones como `DROP`, `ALTER`, `CREATE` sobre la base de datos objetivo para impedir destrucción no deseada de metadatos o estructuras. Todos los DML son ejecutados dentro de una transacción con `ROLLBACK` forzado automático.
