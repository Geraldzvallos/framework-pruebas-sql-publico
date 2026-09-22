# FASE 4.1 — VALIDACIÓN REAL CON ORACLE DATABASE FREE

## Instrucción principal para Antigravity

Lee completamente `AGENTS.md`, `README.md`, `RESULTADO_REVISION_FINAL_FASE_3.md` y este archivo antes de modificar el proyecto. Ejecuta esta Fase 4.1 sobre la carpeta actual del proyecto. No crees otro proyecto, no trabajes fuera de la carpeta actual y no borres el historial ni los documentos existentes.

La línea base aprobada es de **60 pruebas automáticas exitosas**. Primero debes reproducirla. Si no se obtienen las 60 pruebas, detente, registra el problema y corrige únicamente la causa comprobada antes de continuar.

No presentes un plan para pedir otra aprobación. Después de leer y comprobar los prerrequisitos, ejecuta las tareas autorizadas de esta fase. Solo debes detenerte cuando exista un bloqueo externo real, como Docker ausente, Docker detenido, falta de virtualización, imposibilidad de descargar la imagen oficial o recursos insuficientes.

## Objetivo

Demostrar que el framework se conecta a una instancia real y exclusiva de Oracle Database Free, ejecuta casos `SELECT`, `INSERT`, `UPDATE` y `DELETE`, aplica las estrategias `ROW_COUNT` y `EXISTS`, registra `PASS`, `FAIL` y `ERROR`, y garantiza `ROLLBACK` para que las pruebas DML no dejen cambios permanentes.

Esta fase **no incluye todavía el despliegue público**. No modifiques el frontend salvo que una falla real y reproducible de integración lo exija.

## Reglas obligatorias

1. Utiliza Oracle Database Free en un contenedor local mediante Docker Desktop.
2. Prioriza la imagen oficial `container-registry.oracle.com/database/free:latest`.
3. Si el registro de Oracle exige iniciar sesión o aceptar términos, documenta el paso manual exacto y detente. No sustituyas silenciosamente la imagen por una imagen comunitaria.
4. No guardes contraseñas reales en Git, SQLite, código, documentación, capturas ni reportes.
5. Usa variables de entorno para todas las credenciales.
6. La contraseña debe seguir solicitándose al ejecutar o probar una conexión y nunca persistirse.
7. Conserva el `ROLLBACK` obligatorio del motor.
8. No relajes las validaciones de seguridad ni habilites `CREATE`, `ALTER`, `DROP`, `TRUNCATE`, `GRANT`, `REVOKE`, `COMMIT`, `ROLLBACK` o múltiples sentencias desde los casos de prueba.
9. No reemplaces la base interna SQLite por Oracle: Oracle es la base objetivo sometida a pruebas; SQLite continúa almacenando proyectos, perfiles, casos, suites e historial.
10. No inventes resultados. Un escenario solo puede marcarse como validado si se ejecutó realmente y se conserva su salida.

## Paso 1 — Auditoría de la línea base

Ejecuta y registra:

```powershell
python --version
docker --version
docker compose version
python -m pip check
alembic upgrade head
pytest -q
```

Criterio: `pip check` sin dependencias rotas, migraciones correctas y exactamente las 60 pruebas actuales aprobadas antes de añadir pruebas nuevas.

Comprueba también:

```powershell
docker info
```

Si Docker no está instalado o no está funcionando, genera `RESULTADO_FASE_4_1_BLOQUEADO.md` con el diagnóstico y los pasos manuales necesarios. No afirmes que Oracle fue probado.

## Paso 2 — Infraestructura reproducible de Oracle

Crea una estructura clara, por ejemplo:

```text
infra/
  oracle/
    compose.yml
    README.md
    init/
      001_test_schema.sql
```

Requisitos del `compose.yml`:

- imagen oficial de Oracle Database Free;
- nombre de contenedor estable;
- puerto `1521` publicado únicamente para desarrollo local;
- volumen nombrado para los datos de Oracle;
- contraseña recibida desde una variable de entorno, nunca escrita directamente;
- `healthcheck` real;
- política de reinicio apropiada para desarrollo;
- servicio esperado `FREEPDB1`, salvo que la imagen oficial utilizada documente otro valor;
- no publicar Oracle en interfaces externas innecesarias.

Crea `.env.oracle.example` solo con nombres de variables y valores ficticios. Agrega `.env.oracle` y cualquier wallet, certificado, log o volumen local a `.gitignore`.

El `README.md` de Oracle debe explicar los comandos de inicio, estado, logs, detención y conservación del volumen. No debe contener secretos.

## Paso 3 — Esquema exclusivo de pruebas

Prepara un script idempotente que cree un usuario o esquema exclusivo de pruebas y una tabla simple. Usa nombres inequívocos, por ejemplo:

```sql
FRAMEWORK_TEST
FRAMEWORK_TEST_ITEMS (
    ID NUMBER PRIMARY KEY,
    NAME VARCHAR2(100) NOT NULL,
    ACTIVE NUMBER(1) DEFAULT 1 NOT NULL
)
```

El aprovisionamiento administrativo puede usar DDL porque se ejecuta fuera del motor de casos. Los usuarios creados deben tener únicamente los privilegios mínimos necesarios sobre el esquema de pruebas.

El script debe poder ejecutarse varias veces sin destruir información inesperadamente. No uses el usuario `SYS` ni `SYSTEM` como perfil normal del framework.

## Paso 4 — Compatibilidad real de conexión

Usa estos datos de desarrollo como referencia:

```text
Host: 127.0.0.1
Puerto: 1521
Service Name: FREEPDB1
Usuario: FRAMEWORK_TEST
Contraseña: introducida en tiempo de ejecución
```

Verifica mediante el endpoint y la interfaz:

- conexión correcta con contraseña válida;
- error controlado con contraseña incorrecta;
- la contraseña no aparece en la base interna, logs, respuestas ni historial;
- los errores de Oracle son comprensibles y no exponen secretos.

No cambies el contrato actual de perfiles si `host`, `port`, `service_name` y `username` funcionan con Oracle Database Free.

## Paso 5 — Escenarios reales obligatorios

Ejecuta mediante el mismo servicio usado por la interfaz, no directamente con funciones paralelas que eviten la lógica real.

### Escenario A — SELECT y ROW_COUNT: PASS

```sql
SELECT 1 FROM DUAL
```

- validación: `ROW_COUNT`
- esperado: `1`
- resultado requerido: `PASS`

### Escenario B — SELECT y EXISTS: PASS

```sql
SELECT 1 FROM DUAL
```

- validación: `EXISTS`
- esperado: `true`
- resultado requerido: `PASS`

### Escenario C — INSERT con ROLLBACK: PASS

Ejecuta un `INSERT` válido sobre `FRAMEWORK_TEST_ITEMS`, esperando una fila afectada. Después abre una conexión independiente y confirma que la fila no existe, demostrando que el `ROLLBACK` fue real.

### Escenario D — UPDATE con ROLLBACK: PASS

Prepara un registro controlado, ejecuta un `UPDATE` esperando una fila afectada y confirma desde otra conexión que el valor original permanece.

### Escenario E — DELETE con ROLLBACK: PASS

Ejecuta un `DELETE` esperando una fila afectada y confirma desde otra conexión que el registro todavía existe.

### Escenario F — Diferencia entre esperado y obtenido: FAIL

Ejecuta una consulta válida con una expectativa deliberadamente incorrecta. Debe registrarse como `FAIL`, no como `ERROR`.

### Escenario G — SQL inválido: ERROR

Ejecuta una sentencia permitida sintácticamente incorrecta. Debe registrarse como `ERROR` con mensaje controlado.

### Escenario H — Comando peligroso bloqueado: ERROR

Intenta un `DROP TABLE` mediante un caso de prueba. Debe ser rechazado antes de llegar a Oracle y quedar registrado como error de seguridad.

## Paso 6 — Pruebas automatizadas de integración

Agrega pruebas reales separadas y marcadas, por ejemplo `@pytest.mark.oracle_integration`.

Condiciones:

- deben usar variables de entorno;
- deben saltarse explícitamente cuando Oracle no esté habilitado;
- no deben ejecutarse accidentalmente en la suite normal;
- no deben usar mocks para afirmar integración real;
- cada prueba debe dejar Oracle en el mismo estado inicial;
- deben verificar conexión, `ROW_COUNT`, `EXISTS`, `PASS`, `FAIL`, `ERROR`, historial y rollback DML.

La suite normal debe seguir aprobando completamente. Ejecuta dos veces consecutivas:

```powershell
pytest -q
pytest -q
```

Después ejecuta dos veces las pruebas Oracle con la configuración real documentada. No registres como aprobada una prueba omitida (`skipped`).

## Paso 7 — Verificación desde la interfaz

Con Uvicorn activo, comprueba manualmente:

1. crear o seleccionar el proyecto de validación;
2. crear el perfil Oracle sin contraseña persistida;
3. probar la conexión introduciendo la contraseña en el modal;
4. ejecutar individualmente los casos;
5. asociarlos a una suite y ejecutar la suite;
6. verificar los contadores del dashboard;
7. revisar los detalles en Historial;
8. confirmar que el historial distingue `PASS`, `FAIL` y `ERROR`;
9. confirmar `rollback_applied=true` para DML exitoso.

## Paso 8 — Documentación y evidencias

Actualiza `README.md` con una sección “Oracle Database Free para pruebas locales” que contenga requisitos, configuración, comandos y solución de errores comunes.

Genera `RESULTADO_FASE_4_1.md` con:

- fecha y entorno;
- versiones reales;
- archivos añadidos o modificados;
- comandos ejecutados;
- salidas exactas de las pruebas;
- tabla de los escenarios A–H;
- evidencia del rollback de INSERT, UPDATE y DELETE;
- comprobación de que la contraseña no fue almacenada;
- problemas encontrados y solución aplicada;
- riesgos o pendientes reales;
- conclusión `APROBADO` o `BLOQUEADO` sustentada.

No coloques contraseñas, tokens, wallets ni datos sensibles en el reporte.

## Entregables mínimos

- infraestructura reproducible de Oracle local;
- ejemplo seguro de variables de entorno;
- esquema y datos controlados de prueba;
- pruebas de integración Oracle reales;
- `README.md` actualizado;
- `RESULTADO_FASE_4_1.md`;
- suite normal aprobada dos veces;
- suite Oracle aprobada dos veces sin omisiones;
- evidencia verificable de `PASS`, `FAIL`, `ERROR` y `ROLLBACK`.

## Prohibiciones

- No desplegar todavía.
- No crear otro proyecto ni otra arquitectura.
- No cambiar de FastAPI, SQLAlchemy, Pytest, SQLite ni JavaScript.
- No introducir autenticación completa en esta fase.
- No guardar secretos en archivos versionados.
- No borrar pruebas anteriores para obtener un resultado verde.
- No usar mocks en las pruebas etiquetadas como integración Oracle.
- No afirmar éxito si Docker, Oracle o una prueba real no se ejecutaron.

## Criterio de cierre

La Fase 4.1 se considera terminada únicamente cuando Oracle Database Free está activo, la interfaz prueba la conexión, los escenarios reales A–H producen los resultados esperados, el rollback DML se demuestra desde una conexión independiente, todas las pruebas anteriores continúan aprobando y el reporte contiene evidencia exacta.

Al terminar, informa de forma breve qué se comprobó, el total de pruebas normales e integradas, los resultados A–H y la ubicación de `RESULTADO_FASE_4_1.md`. No generes todavía el ZIP final: se hará después de la Fase 4.2 de seguridad y despliegue.
