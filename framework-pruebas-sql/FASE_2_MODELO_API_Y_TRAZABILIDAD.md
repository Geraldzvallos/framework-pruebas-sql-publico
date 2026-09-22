# FASE 2 — Modelo interno, API robusta y trazabilidad

## Framework de pruebas de base de datos SQL

Este archivo es una instrucción de trabajo para Antigravity. Debe colocarse en la raíz del proyecto actual, al mismo nivel que `README.md`, `AGENTS.md` y `requirements.txt`.

---

## 1. Autorización y forma de trabajo

Esta instrucción constituye la aprobación expresa para implementar **únicamente la Fase 2 definida en este documento**. No debes detenerte a solicitar otra aprobación dentro de este alcance.

Antes de modificar código:

1. Lee completamente `AGENTS.md`, `README.md`, `PLAN_REVISION_FRAMEWORK_PRUEBAS_SQL.md` y este archivo.
2. Inspecciona el código y las pruebas actuales.
3. Ejecuta la instalación y las pruebas existentes.
4. Conserva las funcionalidades que ya sirven.

Después, implementa, prueba y documenta la fase completa. No te limites a proponer código ni a crear un diagnóstico: debes realizar los cambios en el proyecto.

Si encuentras una contradicción, respeta este orden de prioridad:

1. Seguridad y no pérdida de datos.
2. Alcance de este archivo.
3. `AGENTS.md`.
4. `README.md` y el plan general.

---

## 2. Estado de partida ya verificado

No repitas una auditoría extensa. Toma como punto de partida estas evidencias:

- La aplicación instala sus dependencias en un entorno virtual limpio.
- `pip check` no reporta dependencias rotas.
- Las 20 pruebas actuales pasan de forma consecutiva.
- Las pruebas no modifican `framework_interno.db`.
- FastAPI inicia y publica 8 rutas actuales.
- El analizador SQL admite `SELECT`, `INSERT`, `UPDATE`, `DELETE`, CTE, comentarios y literales válidos.
- Las operaciones DML exigen un rollback exitoso.
- Las contraseñas no están escritas directamente en el repositorio.

También existen problemas comprobados que esta fase debe corregir:

1. `POST /api/test-cases/` acepta nombre, SQL y resultado esperado vacíos.
2. Agregar dos veces el mismo caso a una suite produce `500 Internal Server Error`.
3. Las paginaciones no tienen límites estrictos.
4. No existen proyectos ni perfiles de conexión persistidos.
5. No existe un endpoint para consultar el historial.
6. El historial actual guarda evidencia insuficiente.
7. La estrategia `ExistenceValidation` existe, pero las ejecuciones siempre usan `RowCountValidation`.
8. La base interna se crea con `create_all`, pero no dispone de migraciones versionadas.
9. El frontend todavía usa una URL local fija y el botón de ejecutar suite solo muestra “Motor en espera”. Esto se completará en la Fase 3; esta fase no debe empeorar su funcionamiento actual.
10. El ZIP de trabajo contiene `venv/`, `.pytest_cache/` y `framework_interno.db`. Estos elementos no deben incluirse en la entrega limpia ni subirse a Git.

---

## 3. Objetivo de esta fase

Completar la base funcional del backend para que el framework pueda:

- organizar pruebas por proyecto;
- registrar configuraciones de conexión Oracle sin almacenar contraseñas;
- seleccionar el tipo de validación de cada caso;
- ejecutar casos y suites mediante un perfil de conexión;
- guardar evidencia técnica completa;
- consultar el historial mediante la API;
- evolucionar la SQLite interna mediante migraciones reproducibles;
- responder con errores HTTP controlados, nunca con errores 500 por entradas previsibles.

Al terminar, el backend debe quedar listo para conectar el frontend en la Fase 3.

---

## 4. Restricciones obligatorias

- Mantén Python, FastAPI, SQLAlchemy, SQLite, Oracle `oracledb`, HTML, CSS, JavaScript, Bootstrap y Pytest.
- Oracle sigue siendo el único motor objetivo del MVP.
- No migres a React, Angular, Supabase, Firebase, PostgreSQL ni otro stack.
- No implementes autenticación, roles, IA, gráficas avanzadas ni reportes PDF.
- No despliegues todavía.
- No ejecutes sentencias contra una base Oracle real durante las pruebas automatizadas.
- No ejecutes DDL peligroso ni alteres datos reales.
- No guardes contraseñas en SQLite, archivos, respuestas, historial o logs.
- No borres datos actuales. Prueba la migración sobre una copia de la SQLite existente.
- No elimines los 20 tests actuales para hacer pasar la suite.
- No ocultes errores con `except Exception: pass`.
- No devuelvas detalles internos, trazas o credenciales al cliente.
- No mezcles la base interna del framework con la base Oracle que se está probando.

---

## 5. Trabajo obligatorio

### 5.1 Corregir validaciones de entrada y errores HTTP

Usa Pydantic con `Field`, validadores o tipos equivalentes para exigir:

- nombres sin espacios vacíos;
- `sql_query` no vacío;
- `expected_result` no vacío y compatible con el tipo de validación;
- `skip >= 0`;
- `1 <= limit <= 100`;
- puerto Oracle entre 1 y 65535;
- host, servicio y usuario no vacíos;
- longitudes máximas razonables para evitar entradas descontroladas.

Normaliza espacios externos cuando corresponda. Una entrada inválida debe responder `422`, no guardarse parcialmente.

Al relacionar suite y caso:

- responde `404` si alguno no existe;
- responde `409` si el caso ya pertenece a la suite;
- responde `409` si pertenecen a proyectos diferentes;
- nunca permitas que una restricción esperable de integridad termine en un error 500.

Maneja `IntegrityError` con rollback de la sesión interna y respuesta controlada.

### 5.2 Modelo `Project`

Crea un modelo de proyecto con, como mínimo:

- `id`;
- `name`;
- `description` opcional;
- `created_at`;
- `updated_at`.

Relaciona el proyecto con casos, suites y perfiles de conexión.

Los registros actuales deben asignarse mediante migración a un proyecto inicial llamado `Proyecto general`. El campo `project_id` debe quedar con integridad referencial y no nulo en los registros definitivos.

Para conservar temporalmente la compatibilidad del frontend actual, si el cliente antiguo omite `project_id` al crear un caso o suite, la capa de servicio debe asignar `Proyecto general`. Documenta este comportamiento como compatibilidad transitoria para la Fase 3.

Implementa API para:

- crear proyecto;
- listar proyectos;
- obtener un proyecto por ID;
- actualizar un proyecto;
- eliminarlo únicamente cuando no tenga datos dependientes; si los tiene, responder `409`.

### 5.3 Modelo `ConnectionProfile` seguro

Crea perfiles de conexión Oracle asociados a un proyecto con:

- `id`;
- `project_id`;
- `name`;
- `engine`, limitado por ahora a `ORACLE`;
- `host`;
- `port`, con valor predeterminado 1521;
- `service_name`;
- `username`;
- `created_at`;
- `updated_at`.

Regla crítica: **no agregues una columna `password`**. La contraseña se recibe solo en la solicitud de probar o ejecutar, se usa en memoria y se descarta.

Implementa API para crear, listar por proyecto, obtener, actualizar y eliminar perfiles. Implementa además:

`POST /api/connections/{connection_id}/test`

El cuerpo debe contener solamente la contraseña necesaria para esa prueba. Construye el DSN de forma segura con `oracledb.makedsn` o una alternativa oficial equivalente, abre la conexión, ejecuta `SELECT 1 FROM DUAL`, cierra cursor y conexión en `finally`, y devuelve un mensaje controlado. No devuelvas ni registres la contraseña.

### 5.4 Tipos de validación utilizables

Agrega a cada caso un campo `validation_type` con un enum o conjunto cerrado de valores:

- `ROW_COUNT`;
- `EXISTS`.

Comportamiento:

- `ROW_COUNT`: `expected_result` debe representar un entero mayor o igual a cero.
- `EXISTS`: `expected_result` debe ser `true` o `false`, sin depender de mayúsculas.

El orquestador debe elegir realmente `RowCountValidation` o `ExistenceValidation` según el caso. No dejes `ExistenceValidation` como código sin uso.

Los casos ya existentes deben migrarse con `validation_type = ROW_COUNT`.

### 5.5 Historial y evidencia completa

Amplía `ExecutionHistory` para conservar, como mínimo:

- `id`;
- `project_id`;
- `test_case_id`;
- `suite_id` opcional;
- `connection_profile_id` opcional;
- `status`: `PASS`, `FAIL` o `ERROR`;
- `executed_at` en UTC;
- `duration_ms`;
- `statement_type`;
- `executed_sql`;
- `validation_type`;
- `expected_result`;
- `actual_result` serializado de forma segura;
- `rowcount`;
- `rollback_applied`;
- `rollback_error` opcional;
- `error_message` opcional.

El resultado real debe ser útil como evidencia, pero debe evitar una respuesta ilimitada. Define y documenta un límite razonable para las filas almacenadas o devueltas y señala si fueron truncadas. Convierte de manera controlada valores habituales de Oracle que no son JSON nativo, por ejemplo fecha, decimal y bytes.

Una ejecución con error también debe registrarse. Un fallo al aplicar rollback en DML debe producir `ERROR`, nunca `PASS`.

Implementa:

`GET /api/history/`

Debe admitir paginación y filtros opcionales por:

- `project_id`;
- `test_case_id`;
- `suite_id`;
- `status`.

Implementa también:

`GET /api/history/{history_id}`

Usa `404` cuando no exista.

### 5.6 Servicio único de ejecución

Actualmente la ejecución individual y la ejecución de suites repiten lógica. Extrae una función o servicio reutilizable que se encargue de:

1. ejecutar el SQL;
2. seleccionar la estrategia de validación;
3. determinar `PASS`, `FAIL` o `ERROR`;
4. preparar la evidencia;
5. persistir el historial.

La ejecución individual y la ejecución de suite deben usar ese mismo servicio.

Permite ejecutar usando `connection_id` más una contraseña enviada en la solicitud. Si conservas temporalmente el formato anterior con DSN y usuario directos para compatibilidad, no dupliques la lógica y documenta qué formato quedará como oficial.

En ejecución de suite:

- todos los casos deben pertenecer al mismo proyecto que la suite;
- reutiliza una sola conexión cuando sea seguro;
- un error de un caso no debe impedir registrar el resumen y los demás casos, salvo que la conexión completa haya quedado inutilizable;
- cada detalle debe guardarse en historial con `suite_id`.

### 5.7 Migraciones reproducibles

Integra Alembic o un mecanismo de migraciones SQLAlchemy equivalente y versionado. Se prefiere Alembic.

La migración debe:

1. crear las tablas nuevas;
2. crear `Proyecto general`;
3. asignar los casos y suites existentes a ese proyecto;
4. agregar los campos nuevos del historial;
5. asignar `ROW_COUNT` a los casos existentes;
6. preservar los registros actuales;
7. incluir una reversión razonable cuando sea técnicamente segura.

Prueba `upgrade` usando una copia de `framework_interno.db`, nunca la única copia de trabajo. Documenta el comando de migración en el README.

Evita que `Base.metadata.create_all()` sea la única estrategia de evolución. Define con claridad cómo se inicializa una base nueva y cómo se actualiza una existente.

### 5.8 Configuración y seguridad

- Centraliza configuración de la base interna, CORS y servidor mediante variables de entorno.
- Mantén `.env.example` solo con valores ficticios.
- No uses `allow_origins=["*"]` junto con credenciales en configuración de producción.
- Permite orígenes locales durante desarrollo y documenta cómo establecer el dominio real en producción.
- La URL del frontend no debe condicionarte a reestructurar toda la interfaz en esta fase; solo evita romperla.
- Sanitiza los mensajes de Oracle que pudieran contener la contraseña.

### 5.9 Entrega limpia

Actualiza `.gitignore` si hace falta para excluir:

- `.env`;
- `venv/` y `.venv/`;
- `__pycache__/`;
- `.pytest_cache/`;
- `*.pyc`;
- `framework_interno.db` y otras SQLite generadas;
- archivos temporales, cobertura y logs.

No borres el entorno virtual que estés usando si es necesario para trabajar. Sin embargo, crea la entrega o ZIP final sin `venv/`, cachés, bases generadas ni secretos.

---

## 6. Pruebas automáticas obligatorias

Conserva las 20 pruebas actuales y agrega pruebas aisladas para, como mínimo:

1. Rechazo de caso con nombre vacío.
2. Rechazo de caso con SQL vacío.
3. Rechazo de `ROW_COUNT` no numérico o negativo.
4. Normalización y validación de `EXISTS`.
5. Límites de paginación.
6. Duplicado caso-suite con respuesta 409.
7. Caso y suite de proyectos diferentes con respuesta 409.
8. CRUD de proyectos.
9. Impedimento de borrar un proyecto con dependencias.
10. CRUD de perfiles Oracle sin campo de contraseña.
11. Confirmación de que una contraseña no aparece en respuesta, base interna ni logs capturados.
12. Prueba de conexión Oracle simulada con mocks, tanto éxito como error.
13. Selección real de las estrategias `ROW_COUNT` y `EXISTS`.
14. Persistencia de evidencia para `PASS`, `FAIL` y `ERROR`.
15. Persistencia de `rollback_applied` en DML.
16. Consulta y filtros del historial.
17. Ejecución de suite con varios casos y resumen coherente.
18. Migración desde una copia del esquema actual sin perder casos, suites, relaciones ni historial.
19. Confirmación de que las pruebas no crean ni modifican `framework_interno.db`.
20. Arranque de la aplicación y disponibilidad de `/`, `/docs` u `openapi.json`.

Usa SQLite aislada en memoria o un archivo temporal para cada prueba. Simula Oracle con mocks; no dependas de una instancia Oracle real ni de internet.

---

## 7. Criterios de aceptación

La Fase 2 se considera terminada solo si se cumplen todos estos puntos:

- La instalación limpia funciona.
- `pip check` no muestra dependencias incompatibles.
- Todas las pruebas anteriores y nuevas pasan dos veces consecutivas.
- La aplicación inicia sin errores.
- Entradas inválidas producen respuestas 4xx correctas, no errores 500.
- La relación caso-suite duplicada está controlada.
- Existen proyectos, perfiles Oracle e historial consultable.
- La contraseña nunca se persiste ni se devuelve.
- `ROW_COUNT` y `EXISTS` funcionan de verdad.
- La ejecución individual y la de suite comparten el servicio central.
- Una migración actualiza una copia de la base existente sin pérdida de datos.
- La SQLite real conserva el mismo hash antes y después de los tests.
- El frontend actual continúa cargando casos y suites.
- El repositorio o ZIP limpio no incluye `venv`, cachés, `.env` ni bases generadas.
- README y `.env.example` reflejan el funcionamiento real, sin afirmar que el frontend o el despliegue ya están terminados.

No declares éxito parcial como “fase completada”. Si algo no puede verificarse, indícalo claramente como pendiente con la causa y la evidencia.

---

## 8. Comandos de verificación esperados

Adapta las rutas a Windows o Linux según el entorno, pero ejecuta equivalentes a:

```bash
python -m venv .venv-audit
python -m pip install -r requirements.txt
python -m pip check
python -m pytest -q
python -m pytest -q
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Incluye también el comando real de Alembic usado para actualizar una copia de la base y la verificación de integridad de sus registros.

---

## 9. Entrega obligatoria de Antigravity

Al terminar, crea en la raíz un archivo llamado:

`RESULTADO_FASE_2.md`

Debe contener:

1. Resumen ejecutivo.
2. Estado final: completada, parcial o bloqueada.
3. Lista exacta de archivos creados y modificados.
4. Cambios de modelos y relaciones.
5. Rutas API disponibles con método, ruta y finalidad.
6. Política aplicada para no almacenar contraseñas.
7. Migración creada y cómo ejecutarla.
8. Comandos ejecutados.
9. Número total de pruebas y resultado textual real.
10. Evidencia de dos ejecuciones consecutivas de Pytest.
11. Evidencia de que la SQLite real no cambió durante los tests.
12. Evidencia del arranque de FastAPI.
13. Pruebas manuales realizadas.
14. Pendientes reales, sin ocultarlos.
15. Recomendación concreta para la Fase 3: frontend funcional conectado a proyectos, perfiles, ejecuciones e historial.

Además, entrega una copia limpia del proyecto. No incluyas `venv/`, `.venv/`, `.pytest_cache/`, `__pycache__/`, `.env`, archivos de log ni `framework_interno.db`.

---

## 10. Instrucción final

Trabaja directamente sobre la carpeta actual y completa la Fase 2 de principio a fin. Haz cambios pequeños y verificables, mantén el código entendible para un proyecto universitario y no añadas funciones fuera del alcance.

Tu prioridad es que el backend sea correcto, seguro, reproducible y comprobable. El frontend integral y el despliegue pertenecen a las fases siguientes.
