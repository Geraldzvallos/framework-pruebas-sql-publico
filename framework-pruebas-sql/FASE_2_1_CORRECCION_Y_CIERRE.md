# FASE 2.1 — Corrección, verificación y cierre real de la Fase 2

## Framework de pruebas de base de datos SQL

Coloca este archivo en la raíz del proyecto actual, junto a `AGENTS.md`, `README.md`, `FASE_2_MODELO_API_Y_TRAZABILIDAD.md` y `requirements.txt`.

---

## 1. Autorización

Este documento autoriza implementar únicamente la **Fase 2.1 de corrección y cierre**. No avances al frontend integral ni al despliegue.

Lee primero:

1. `AGENTS.md`.
2. `README.md`.
3. `FASE_2_MODELO_API_Y_TRAZABILIDAD.md`.
4. `RESULTADO_FASE_2.md`.
5. Este documento.

Después corrige directamente el proyecto. No entregues solo un diagnóstico ni solicites aprobación adicional dentro de este alcance.

---

## 2. Estado comprobado externamente

La revisión independiente confirmó lo siguiente:

### Funciones que sí pasan

- Instalación limpia completada.
- `pip check` sin dependencias rotas.
- 34 pruebas actuales pasan dos veces: `34 passed`.
- El hash de la SQLite entregada no cambia durante esas dos ejecuciones.
- FastAPI inicia y publica 16 rutas.
- Existen modelos y endpoints para proyectos, conexiones, casos, suites e historial.
- La contraseña no existe como columna de `connection_profiles`.
- `ROW_COUNT` y `EXISTS` están conectados al servicio de ejecución.

### Problemas reproducidos que impiden aprobar la Fase 2

1. **Alembic falla en una base vacía:** `sqlalchemy.exc.NoSuchTableError: test_cases`.
2. **Alembic falla sobre la base entregada sin versión:** `sqlite3.OperationalError: table projects already exists`.
3. **La migración sobre una base antigua devuelve código 0, pero no queda aplicada:** `alembic_version` permanece vacío, no se crea `connection_profiles`, no se agregan columnas y `Proyecto general` no queda persistido.
4. La prueba obligatoria de migración desde el esquema anterior no existe, aunque `RESULTADO_FASE_2.md` afirma que fue realizada.
5. `app/main.py` ejecuta `Base.metadata.create_all()` y crea `Proyecto general` durante la importación. Esto compite con Alembic y produce efectos secundarios.
6. `tests/conftest.py` define `FRAMEWORK_DB_URL` después de importar `app.core.database` y `app.main`; por lo tanto, la configuración aislada llega demasiado tarde.
7. La prueba del hash solo lee dos veces el mismo archivo sin ejecutar acciones entre ambas lecturas; no demuestra aislamiento por sí sola.
8. `PUT /api/test-cases/{id}` acepta un nombre compuesto solo por espacios, guarda el dato inválido y termina en HTTP 500 al validar la respuesta.
9. Las actualizaciones parciales de casos no validan correctamente la combinación `validation_type` + `expected_result`.
10. La API permite crear un perfil con `engine = MYSQL`, aunque el MVP solo admite Oracle.
11. Se puede ejecutar un caso del proyecto A usando un perfil de conexión del proyecto B y la API responde 200.
12. Tras crear historial y eliminar el caso, eliminar el proyecto produce HTTP 500 porque no se verifica el historial dependiente.
13. No todas las escrituras controlan `IntegrityError` con `db.rollback()`.
14. `CORS_ORIGINS` se usa en el código, pero no aparece en `.env.example`; el valor predeterminado continúa siendo `*` con credenciales habilitadas.
15. El README afirma que el frontend gestiona proyectos, conexiones e historial, pero `frontend/app.js` no llama a esos endpoints y el botón de suite continúa mostrando “Motor en Espera”.
16. El ZIP entregado no es limpio: incluye `venv/`, `.pytest_cache/`, `__pycache__/`, archivos `.pyc` y `framework_interno.db`.

No discutas estos resultados ni los sustituyas por las pruebas existentes. Debes agregar pruebas que los reproduzcan y luego corregirlos.

---

## 3. Objetivo

Cerrar correctamente la Fase 2 mediante:

- una ruta de migración reproducible y segura;
- validaciones completas para creación y actualización;
- integridad entre proyectos, casos, suites, conexiones e historial;
- configuración sin valores inseguros o engañosos;
- pruebas que realmente aíslen la SQLite de trabajo;
- documentación veraz;
- un ZIP final limpio.

No agregues nuevas funcionalidades de negocio fuera de estas correcciones.

---

## 4. Corrección obligatoria de Alembic

### 4.1 Escenarios que deben funcionar

La solución debe soportar y probar estos tres escenarios con archivos temporales independientes:

1. **Base vacía:** `alembic upgrade head` debe crear el esquema final completo, insertar `Proyecto general` y registrar la revisión actual.
2. **Base heredada de Fase 1:** debe conservar casos, suites, asociaciones e historial; luego debe agregar las tablas y columnas de Fase 2, asignar `project_id = 1`, asignar `validation_type = ROW_COUNT` y registrar la revisión.
3. **Base Fase 2 sin `alembic_version`:** debe reconocer de forma segura el esquema ya creado, completar cualquier elemento faltante sin duplicar tablas ni columnas y registrar la revisión.

No uses la base original para experimentar. Trabaja con copias temporales y compara cantidades y registros antes y después.

### 4.2 Transacciones de la migración

Revisa `alembic/env.py`. La ejecución actual de `PRAGMA foreign_keys=OFF` inicia una transacción que no queda confirmada correctamente y provoca una migración aparentemente exitosa pero revertida.

Corrige la gestión transaccional para que:

- la migración confirme todos sus cambios;
- `alembic_version` contenga exactamente la revisión de `head`;
- `PRAGMA foreign_key_check` no reporte errores;
- las claves foráneas vuelvan a quedar activadas;
- un fallo real produzca código de salida distinto de cero.

No marques manualmente una base como actualizada sin validar primero que contiene todas las tablas, columnas, índices, relaciones y datos obligatorios.

### 4.3 Alembic como autoridad del esquema

- Elimina de `app/main.py` la creación automática de tablas mediante `Base.metadata.create_all(bind=engine)`.
- Elimina la inserción de `Proyecto general` como efecto secundario al importar la aplicación.
- La migración debe crear el esquema y los datos iniciales.
- Las pruebas pueden utilizar `Base.metadata.create_all()` solamente sobre su base temporal aislada.
- Si la aplicación inicia sin que la base esté migrada, devuelve o registra un mensaje claro de configuración; no construyas silenciosamente un esquema paralelo.
- Documenta un único flujo oficial para preparar la base antes de iniciar FastAPI.

---

## 5. Corrección de validaciones y API

### 5.1 Actualización de casos

`TestCaseUpdate` debe aplicar las mismas reglas que la creación:

- nombre no vacío después de `strip()`;
- SQL no vacío después de `strip()`;
- longitudes máximas;
- `ROW_COUNT` exige entero mayor o igual a cero;
- `EXISTS` exige `true` o `false` y lo normaliza;
- cambiar solamente `validation_type` debe validar también el `expected_result` que ya está almacenado;
- cambiar solamente `expected_result` debe validarse contra el tipo almacenado.

Para una actualización parcial, combina primero los datos actuales con los cambios solicitados y valida el estado final completo antes de escribir. Una entrada inválida debe responder 422 y no modificar la base.

### 5.2 Perfiles Oracle

- Define `engine` con un enum o `Literal` que permita únicamente `ORACLE`.
- Rechaza `MYSQL`, `POSTGRESQL`, valores vacíos y cualquier motor no implementado con 422.
- Aplica `strip()` y validación de espacios a nombre, host, servicio y usuario tanto en creación como actualización.
- Verifica `project_id > 0`.
- Conserva la regla de no almacenar contraseñas.

### 5.3 Integridad entre proyectos

Antes de ejecutar un caso o suite mediante `connection_profile_id`:

- comprueba que el perfil existe;
- comprueba que pertenece al mismo proyecto del caso o suite;
- responde 404 si no existe;
- responde 409 si pertenece a otro proyecto;
- realiza estas comprobaciones antes de intentar conectarse a Oracle.

En ejecución de suite, verifica además que todos sus casos pertenecen al proyecto de la suite.

### 5.4 Eliminaciones e historial

- Considera `execution_histories` al decidir si un proyecto puede eliminarse.
- Si conserva historial, responde 409 con explicación clara.
- Nunca dejes que una restricción de integridad previsible produzca 500.
- Captura `IntegrityError`, ejecuta `db.rollback()` y responde con 409 cuando corresponda.
- Mantén la evidencia histórica: no uses eliminación en cascada para borrar ejecuciones silenciosamente.

### 5.5 Errores y filtros

- Valida identificadores y filtros numéricos como enteros positivos cuando corresponda.
- Limita el filtro de estado a `PASS`, `FAIL` y `ERROR`; un valor desconocido debe responder 422.
- Evita interpolar mensajes internos innecesarios de Oracle, SQLAlchemy o DSN en respuestas públicas.
- Ninguna entrada inválida previsible debe responder 500.

### 5.6 Operaciones útiles para la Fase 3

Completa solamente estas omisiones de CRUD ya previstas por los esquemas actuales:

- `PUT /api/suites/{suite_id}` para editar nombre y descripción con validación.
- `DELETE /api/suites/{suite_id}/test-cases/{test_case_id}` para retirar un caso de una suite sin borrar el caso.

No construyas todavía las pantallas del frontend.

---

## 6. Aislamiento real de pruebas

Corrige `tests/conftest.py` para establecer la URL de prueba **antes de importar cualquier módulo `app.*`**.

Las pruebas deben:

- utilizar SQLite temporal o en memoria;
- no importar `app.main` con la URL real cargada;
- no crear tablas ni proyectos en `framework_interno.db` durante colección;
- comprobar el hash real antes y después de todo el proceso relevante, no dos veces seguidas sin operaciones intermedias;
- ejecutar las migraciones en un subproceso o contexto limpio con una URL temporal;
- simular Oracle con mocks.

Agrega pruebas explícitas para cada problema enumerado en este documento.

---

## 7. Configuración y CORS

- Agrega `CORS_ORIGINS` a `.env.example` con orígenes locales explícitos.
- No uses simultáneamente `allow_origins=["*"]` y `allow_credentials=True`.
- Si permites `*` en un modo especial, desactiva credenciales en ese modo.
- Define orígenes locales seguros como valor de desarrollo.
- Si se indica copiar `.env`, agrega y configura una carga real del archivo, por ejemplo mediante `python-dotenv`, o corrige la documentación para usar variables del sistema. No documentes un mecanismo que el programa ignora.
- Retira de `.env.example` variables Oracle que el código no utiliza o documenta exactamente dónde se usan.
- Nunca agregues contraseñas reales.

---

## 8. README veraz

Actualiza el README para indicar claramente:

- backend de Fase 2 disponible;
- frontend actual limitado a visualizar/crear/eliminar casos y listar suites;
- ejecución desde el frontend todavía pendiente;
- pantallas de proyectos, conexiones e historial pendientes para Fase 3;
- Oracle real todavía no verificado si no existe una instancia de pruebas disponible;
- comando exacto para migrar una base nueva y una base heredada;
- método real de carga de variables de entorno;
- prohibición de usar una base Oracle de producción.

No afirmes “100 % completado” ni “frontend interactivo completo” sin evidencia reproducible.

---

## 9. Entrega limpia

No borres el entorno o la SQLite de trabajo del usuario. Genera una copia de entrega independiente que excluya:

- `venv/`;
- `.venv/` y cualquier entorno de auditoría;
- `.pytest_cache/`;
- `__pycache__/`;
- `*.pyc`;
- `.env`;
- `framework_interno.db` y otras bases generadas;
- logs, cobertura y archivos temporales.

El ZIP limpio debe incluir código, migraciones, pruebas, `.env.example`, documentación y archivos `.md` de resultados.

Comprueba el contenido del ZIP después de crearlo. No basta con que `.gitignore` sea correcto.

---

## 10. Pruebas de aceptación obligatorias

Además de conservar las 34 pruebas actuales, agrega pruebas para:

1. Migración de base vacía hasta `head`.
2. Migración de una base heredada con conservación exacta de datos.
3. Adopción segura de una base Fase 2 sin tabla/versionado Alembic.
4. `alembic_version` igual a la revisión `head` en los tres escenarios.
5. `PRAGMA foreign_key_check` sin resultados.
6. Importar o iniciar FastAPI sin crear/modificar silenciosamente la SQLite.
7. Actualizar nombre de caso con espacios: 422 y dato anterior intacto.
8. Actualizar SQL con espacios: 422 y dato anterior intacto.
9. Actualizar a combinaciones inválidas de tipo y resultado: 422 sin persistencia parcial.
10. Crear perfil con `MYSQL`: 422.
11. Actualizar perfil con cadenas vacías o espacios: 422.
12. Ejecutar caso con perfil de otro proyecto: 409 y sin llamada a Oracle.
13. Ejecutar suite con perfil de otro proyecto: 409 y sin llamada a Oracle.
14. Eliminar proyecto que conserva historial: 409.
15. Filtro de historial con estado inválido: 422.
16. Editar una suite correctamente.
17. Retirar un caso de una suite; repetir la operación debe responder de forma controlada.
18. Confirmar que ninguna contraseña aparece en respuestas, base o logs capturados.
19. Ejecutar toda la suite dos veces consecutivas.
20. Arrancar FastAPI sobre una base correctamente migrada y comprobar `/`, `/docs` y `/openapi.json`.
21. Inspeccionar el ZIP limpio y confirmar que no contiene los elementos excluidos.

No elimines ni debilites pruebas para obtener un resultado verde.

---

## 11. Comandos y evidencia mínima

Ejecuta equivalentes adecuados al sistema operativo:

```bash
python -m venv .venv-audit
python -m pip install -r requirements.txt
python -m pip check
python -m pytest -q
python -m pytest -q
alembic upgrade head
alembic current
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Los comandos de Alembic deben ejecutarse por separado contra:

- una base vacía temporal;
- una copia de la base heredada;
- una copia de la base Fase 2 sin versión.

Registra códigos de salida, revisión resultante, tablas, columnas, conteos y `foreign_key_check`.

---

## 12. Entregables

Al terminar, entrega:

1. Proyecto corregido.
2. `RESULTADO_FASE_2_1.md`.
3. ZIP limpio del proyecto.

`RESULTADO_FASE_2_1.md` debe incluir:

- estado real: completada, parcial o bloqueada;
- archivos modificados;
- causa raíz de cada error;
- solución aplicada;
- evidencia de los tres escenarios de migración;
- conteos antes y después de migrar la base heredada;
- contenido de `alembic_version`;
- resultado de `foreign_key_check`;
- total real de pruebas y dos ejecuciones consecutivas;
- evidencia de arranque;
- prueba del aislamiento de SQLite;
- resultado de inspección del ZIP;
- pendientes reales para la Fase 3.

No declares la fase completada si cualquiera de los tres escenarios de migración falla, existe algún 500 reproducido en este documento o el ZIP continúa incluyendo archivos excluidos.

---

## 13. Instrucción final para Antigravity

Corrige la Fase 2 directamente sobre el proyecto actual. Prioriza integridad de datos, migraciones reproducibles y errores controlados. Mantén la arquitectura y las tecnologías actuales. No implementes todavía el frontend integral ni realices despliegue.

Cuando todo pase, genera `RESULTADO_FASE_2_1.md` y el ZIP limpio. Si algo queda bloqueado, repórtalo con evidencia exacta y sin afirmar un cumplimiento del 100 %.
