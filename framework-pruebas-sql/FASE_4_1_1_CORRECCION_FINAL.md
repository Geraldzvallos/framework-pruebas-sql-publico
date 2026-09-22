# FASE 4.1.1 — CORRECCIÓN FINAL Y CIERRE DE ORACLE REAL

## Instrucción principal para Antigravity

Lee completamente `AGENTS.md`, `README.md`, `FASE_4_1_ORACLE_REAL.md`, `RESULTADO_FASE_4_1.md` y este documento. Trabaja únicamente sobre la carpeta actual `framework-pruebas-sql-main`; no crees otro proyecto ni otra carpeta de desarrollo.

Esta tarea ya autoriza las correcciones indicadas. Presenta un plan breve y continúa sin esperar otra aprobación. No despliegues todavía, no cambies la arquitectura y no reescribas el backend o frontend que ya funciona.

La línea base comprobada externamente es:

- instalación desde `requirements.txt`: correcta;
- `pip check`: sin dependencias rotas;
- migración: `002 (head)`;
- frontend JavaScript: sintaxis válida;
- `/`, `/docs`, `/openapi.json` y `/ui/`: respuesta `200`;
- suite normal: `60 passed, 8 deselected` dos veces.

Conserva esas 60 pruebas. Corrige en una sola intervención todos los puntos siguientes.

## 1. Eliminar cualquier contraseña de respaldo del código

En `tests/test_fase4_oracle.py` existe una contraseña escrita como valor predeterminado de `FRAMEWORK_TEST_PASSWORD`. Elimínala completamente.

Las pruebas Oracle solo deben habilitarse cuando se cumplan simultáneamente estas condiciones:

- `RUN_ORACLE_TESTS=1`;
- `FRAMEWORK_TEST_PASSWORD` existe y no está vacía;
- las demás variables obligatorias están disponibles.

Usa variables de entorno para:

- `ORACLE_HOST` — valor local predeterminado permitido: `127.0.0.1`;
- `ORACLE_PORT` — valor local predeterminado permitido: `1521`;
- `ORACLE_SERVICE` — valor local predeterminado permitido: `FREEPDB1`;
- `ORACLE_TEST_USER` — valor local predeterminado permitido: `FRAMEWORK_TEST`;
- `FRAMEWORK_TEST_PASSWORD` — sin valor predeterminado;
- `RUN_ORACLE_TESTS` — desactivado por defecto.

No uses `ORACLE_PWD` como interruptor de las pruebas: esa clave corresponde a la cuenta administrativa del contenedor, no al usuario que ejecuta las pruebas.

Actualiza `.env.oracle.example` sin poner contraseñas reales. Incluye valores ficticios claramente identificados y `RUN_ORACLE_TESTS=0`.

## 2. Restringir Oracle al equipo local

En `infra/oracle/compose.yml`, cambia la publicación del puerto para que Oracle solo escuche desde el host local:

```yaml
ports:
  - "127.0.0.1:1521:1521"
```

Conserva el volumen, el `healthcheck`, `FREEPDB1` y la imagen oficial.

## 3. Aplicar privilegios mínimos al usuario de pruebas

En `infra/oracle/init/001_test_schema.sh` no otorgues `CONNECT`, `RESOURCE` ni cuota ilimitada.

El usuario `FRAMEWORK_TEST` debe recibir únicamente:

- `CREATE SESSION`;
- una cuota pequeña y finita sobre `USERS`, suficiente para la tabla de prueba, por ejemplo `10M`.

El script debe seguir siendo idempotente y debe crear `FRAMEWORK_TEST_ITEMS` sin destruir datos inesperadamente. El framework nunca debe utilizar `SYS` o `SYSTEM` como perfil normal.

## 4. Corregir la documentación

En `infra/oracle/README.md`, reemplaza la referencia incorrecta `ORACLE_PASSWORD` por `ORACLE_PWD`.

Actualiza el README principal y el de Oracle para explicar claramente:

1. copiar `.env.oracle.example` como `.env.oracle`;
2. establecer `ORACLE_PWD` y `FRAMEWORK_TEST_PASSWORD`;
3. iniciar Oracle desde `infra/oracle`;
4. esperar el estado `healthy`;
5. activar `RUN_ORACLE_TESTS=1` solo para ejecutar integración real;
6. ejecutar por separado pruebas normales y pruebas Oracle;
7. no compartir ni comprimir `.env.oracle`.

No escribas ninguna contraseña real en la documentación.

## 5. Completar las pruebas de integración que faltan

Mantén los escenarios A–H existentes y agrega pruebas reales, sin mocks, para verificar:

### 5.1 Conexión correcta

- Crear un proyecto y un perfil Oracle mediante la API.
- Llamar a `/api/connections/{id}/test` con la contraseña recibida desde el entorno.
- Esperar `200` y una consulta real `SELECT 1 FROM DUAL`.

### 5.2 Contraseña incorrecta

- Llamar al mismo endpoint con una contraseña deliberadamente incorrecta.
- Esperar un error controlado `400`.
- Comprobar que ni la contraseña correcta ni la incorrecta aparezcan en la respuesta, logs, perfil, historial o base SQLite.

### 5.3 Historial real

- Después de ejecutar casos `PASS`, `FAIL` y `ERROR`, consultar el endpoint de historial.
- Verificar que persiste el estado, SQL ejecutado, expectativa, resultado, tipo de sentencia y `rollback_applied`.
- Confirmar que no persiste ninguna contraseña.

### 5.4 Suite real

- Crear mediante la API un proyecto, perfil, casos y una suite.
- Asociar los casos a la suite.
- Ejecutar `/api/execute/suite/{id}` contra Oracle real.
- Verificar el resumen, sus detalles y los registros correspondientes del historial.

### 5.5 Bloqueo de SQL peligroso

- Mantener el escenario `DROP TABLE`.
- Confirmar desde una conexión Oracle independiente que `FRAMEWORK_TEST_ITEMS` continúa existiendo después del intento.

Las pruebas deben cerrar cursores y conexiones aun cuando una aserción falle. Usa `try/finally` o fixtures apropiadas.

## 6. Separar correctamente las suites

La suite normal nunca debe intentar conectarse a Oracle accidentalmente.

Ejecuta dos veces:

```powershell
pytest -q -m "not oracle_integration"
pytest -q -m "not oracle_integration"
```

Resultado obligatorio en cada ejecución:

```text
60 passed
```

Con el contenedor `healthy`, `.env.oracle` configurado y `RUN_ORACLE_TESTS=1`, ejecuta dos veces:

```powershell
pytest -q -m oracle_integration
pytest -q -m oracle_integration
```

No aceptes `skipped`, `xfailed` ni pruebas omitidas en estas dos ejecuciones. Registra las salidas exactas.

Finalmente ejecuta la selección completa autorizada y documenta claramente cuántas pruebas normales y Oracle aprobaron.

## 7. Verificación desde la interfaz

Con Uvicorn y Oracle activos, comprueba realmente desde `/ui/`:

1. seleccionar el proyecto Oracle;
2. crear o seleccionar el perfil `FRAMEWORK_TEST`;
3. probar conexión con contraseña correcta;
4. comprobar el mensaje controlado con contraseña incorrecta;
5. ejecutar un caso `SELECT`;
6. ejecutar un caso DML y comprobar `rollback_applied=true`;
7. ejecutar una suite;
8. visualizar `PASS`, `FAIL` y `ERROR` en Historial.

No captures ni muestres la contraseña. Documenta cada resultado en el informe, diferenciando pruebas automatizadas y comprobación manual.

## 8. Corregir el empaquetador seguro

Actualiza `scripts/build_clean_zip.py` para excluir siempre:

- `.git`;
- cualquier `venv`, `.venv*`, caché o `__pycache__`;
- `.pytest_cache`;
- `.env` y todos los `.env.*`, excepto archivos cuyo nombre termine en `.example`;
- bases `.db`, `.sqlite` y `.sqlite3`;
- logs, cobertura, archivos compilados y ZIP anteriores.

El empaquetador actual no debe poder incluir `.env.oracle`. Agrega una comprobación que falle si cualquier archivo sensible aparece en el ZIP.

Genera solamente un ZIP limpio de revisión llamado:

```text
Fase_4_1_CORREGIDA_Limpio.zip
```

Este ZIP no es todavía el despliegue final de la Fase 4.2.

## 9. Informe corregido

Genera `RESULTADO_FASE_4_1_CORREGIDA.md` con:

- archivos modificados;
- versiones y comandos reales;
- salidas exactas de ambas ejecuciones normales;
- salidas exactas de ambas ejecuciones Oracle;
- tabla de escenarios A–H;
- conexión válida e inválida;
- ejecución de suite e historial;
- evidencia del rollback mediante conexión independiente;
- confirmación de que `FRAMEWORK_TEST_ITEMS` sobrevivió al intento de `DROP`;
- verificación de que ninguna contraseña fue persistida o empaquetada;
- cantidad de entradas del ZIP y lista de exclusiones comprobadas;
- cualquier limitación real, sin inventar resultados.

Corrige también la expresión errónea “Rollins de Seguridad DML” por “rollback de seguridad para DML”.

## 10. Entrega y límites

Entrega únicamente:

- `Fase_4_1_CORREGIDA_Limpio.zip`;
- `RESULTADO_FASE_4_1_CORREGIDA.md`.

No despliegues, no agregues autenticación todavía, no borres el volumen de Oracle y no modifiques funciones ajenas a estos hallazgos.

La fase solo puede declararse `APROBADA` si las 60 pruebas normales pasan dos veces, todas las pruebas Oracle pasan dos veces sin omisiones, la interfaz completa el recorrido indicado, el puerto queda limitado a `127.0.0.1`, no existen contraseñas en el código o ZIP y el informe coincide con los resultados reales.
