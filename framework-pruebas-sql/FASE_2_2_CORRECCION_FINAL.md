# FASE 2.2 — Corrección final de instalación, migraciones y entrega

## Framework de pruebas de base de datos SQL

Coloca este archivo en la raíz del proyecto actual. Esta instrucción autoriza implementar únicamente las correcciones descritas aquí. No avances todavía al frontend de la Fase 3 ni al despliegue.

---

## 1. Estado verificado

La revisión externa del archivo `Fase_2_1_Limpio.zip` confirmó:

- El código conserva 45 pruebas y las 45 pasan dos veces cuando se instala manualmente `python-dotenv`.
- Las correcciones de validación, relaciones entre proyectos y endpoints nuevos están presentes.
- Los tres comandos de migración terminan con código 0.

Sin embargo, la Fase 2.1 no puede aprobarse por estos errores reproducibles:

1. `pip install -r requirements.txt` falla porque la línea `python-dotenv==1.2.3` fue añadida con bytes UTF-16/NUL dentro de un archivo UTF-8.
2. Una base vacía migrada crea `suite_test_cases`, pero el modelo SQLAlchemy utiliza `suite_test_case`.
3. En una base vacía, `execution_history` no contiene `duration_ms` ni `executed_sql`, aunque el modelo y la API requieren ambas columnas.
4. Después de migrar una base vacía:
   - `GET /api/history/` responde 500;
   - ejecutar un caso responde 500;
   - crear o listar una suite con datos responde 500.
5. Solo existe una prueba automática de migración vacía y comprueba pocas tablas. No prueba el esquema completo ni el funcionamiento de la API posterior.
6. No existen pruebas reales de migración de la base heredada ni de la base Fase 2 sin versión, aunque el informe afirma que los tres escenarios fueron validados.
7. El ZIP denominado limpio contiene 921 entradas, de las cuales 879 pertenecen a `venv`, cachés, compilados u otros elementos excluidos.
8. El ZIP guarda rutas internas con `\` de Windows; `unzip` en Linux termina con advertencia y código distinto de cero.
9. El README continúa afirmando que el frontend gestiona proyectos, conexiones e historial, aunque `frontend/app.js` no los utiliza y la ejecución de suites sigue en “Motor en Espera”.
10. `app/main.py` conserva como valor predeterminado CORS `*` con `allow_credentials=True`.
11. `RESULTADO_FASE_2_1.md` reporta solo 11 pruebas de la fase y no presenta la ejecución completa real de 45 pruebas.

Debes corregir estos puntos sin eliminar ni debilitar pruebas existentes.

---

## 2. Corregir `requirements.txt`

- Convierte todo `requirements.txt` a UTF-8 sin BOM y sin bytes NUL.
- Conserva las dependencias actuales.
- Añade correctamente una sola línea de texto:

```text
python-dotenv==1.2.3
```

- No dupliques la dependencia.
- Comprueba el archivo desde una terminal nueva.
- Debe funcionar exactamente:

```bash
python -m venv .venv-audit
python -m pip install -r requirements.txt
python -m pip check
```

No uses una instalación manual separada para ocultar un `requirements.txt` defectuoso.

---

## 3. Crear una migración correctiva `002`

No reutilices silenciosamente el identificador de una migración que ya pudo haberse aplicado. Conserva `001_fase2_schema_and_seed` y crea una revisión posterior, por ejemplo:

```text
002_phase2_schema_alignment
```

La revisión `002` debe reparar bases que ya quedaron marcadas con la revisión 001 y también permitir una instalación nueva mediante `alembic upgrade head`.

### 3.1 Tabla de asociación

El nombre canónico utilizado por el modelo es:

```text
suite_test_case
```

La migración debe manejar estas situaciones:

- Si existe únicamente `suite_test_cases`, renombrarla o migrar sus datos a `suite_test_case`.
- Si existen ambas tablas, copiar asociaciones sin duplicados hacia `suite_test_case` y retirar la tabla incorrecta de forma segura.
- Si no existe ninguna, crear `suite_test_case` con las claves foráneas y clave primaria compuesta correctas.
- No perder asociaciones existentes.

Al finalizar no debe quedar `suite_test_cases`.

### 3.2 Historial

`execution_history` debe coincidir con `app/models/history.py` e incluir como mínimo:

- `id`;
- `project_id`;
- `test_case_id`;
- `suite_id`;
- `connection_profile_id`;
- `status`;
- `executed_at`;
- `duration_ms`;
- `statement_type`;
- `executed_sql`;
- `validation_type`;
- `expected_result`;
- `actual_result`;
- `rowcount`;
- `rollback_applied`;
- `rollback_error`;
- `error_message`.

Agrega `duration_ms` y `executed_sql` cuando falten. Para una tabla existente, utiliza valores temporales seguros que permitan la migración sin borrar historial. Después conserva las restricciones compatibles con el modelo.

### 3.3 Alineación completa

Compara automáticamente `Base.metadata` con el esquema migrado mediante `sqlalchemy.inspect` y verifica:

- nombres de tablas;
- nombres de columnas;
- nulabilidad necesaria;
- claves primarias;
- claves foráneas principales;
- tabla de asociación singular;
- revisión de Alembic igual a `head`;
- `PRAGMA foreign_key_check` vacío.

No basta con verificar que existan `projects`, `test_cases` y `alembic_version`.

---

## 4. Probar los tres escenarios completos

Crea pruebas automatizadas independientes para:

### Escenario A: base vacía

1. Crear un archivo SQLite temporal vacío.
2. Ejecutar `alembic upgrade head` en un subproceso.
3. Validar el esquema completo.
4. Iniciar la API contra esa base.
5. Crear proyecto, perfil, caso y suite.
6. Asociar el caso a la suite.
7. Simular Oracle y ejecutar el caso.
8. Consultar el historial.
9. Confirmar que todas las respuestas esperadas son 2xx y no 500.

### Escenario B: base heredada de Fase 1

1. Construir mediante fixture el esquema anterior con datos representativos.
2. Guardar conteos y valores antes de migrar.
3. Ejecutar `alembic upgrade head`.
4. Confirmar conservación exacta de casos, suites, asociaciones e historial.
5. Confirmar asignación a `Proyecto general` y `ROW_COUNT`.
6. Validar el esquema final y la API.

### Escenario C: base Fase 2 marcada en 001 o sin versión

1. Crear un esquema equivalente al producido anteriormente, incluyendo la tabla plural incorrecta cuando corresponda.
2. Ejecutar `alembic upgrade head`.
3. Confirmar que `002` corrige la tabla y las columnas faltantes.
4. Verificar que los datos no se pierden.
5. Validar el esquema final y la API.

Las tres pruebas deben formar parte de `pytest`; no las marques como “verificadas manualmente”.

---

## 5. Configuración y documentación

### CORS

- Usa como valor predeterminado orígenes locales explícitos, no `*`.
- No combines `allow_origins=["*"]` con `allow_credentials=True`.
- Si una configuración especial permite `*`, desactiva credenciales automáticamente.
- Mantén `CORS_ORIGINS` documentado en `.env.example`.

### README

Corrige el README para indicar con sinceridad:

- Backend de Fase 2 disponible.
- Frontend actual todavía limitado.
- Pantallas de proyectos, conexiones, ejecución e historial pendientes para Fase 3.
- Botón de ejecución de suites todavía no conectado.
- Oracle real pendiente si no se probó con una instancia real.
- Total real de pruebas de la suite completa.
- Flujo correcto: instalar, copiar/configurar `.env`, ejecutar `alembic upgrade head`, iniciar FastAPI.

No afirmes que el frontend integral está terminado.

---

## 6. Crear un ZIP realmente limpio y portable

Genera el archivo:

```text
Fase_2_2_Limpio.zip
```

No uses una compresión indiscriminada de toda la carpeta. Se recomienda crear un script reproducible como `scripts/build_clean_zip.py` utilizando `zipfile`.

El script debe:

- recorrer solamente archivos permitidos;
- excluir directorios completos antes de agregarlos;
- guardar rutas ZIP con `/` mediante `relative_path.as_posix()`;
- evitar rutas absolutas o `..`;
- no incluir el propio ZIP de salida.

Exclusiones obligatorias:

- `venv/`, `.venv/`, `.venv-audit/` y cualquier entorno virtual;
- `.pytest_cache/`;
- `__pycache__/`;
- `*.pyc`, `*.pyo` y `*.pyd`;
- `.env`;
- `*.db`, `*.sqlite` y `*.sqlite3`;
- logs, cobertura, temporales y ZIP anteriores.

Después de crear el ZIP, ábrelo de nuevo mediante Python y falla si:

- aparece alguna exclusión;
- una ruta contiene `\`;
- una ruta es absoluta;
- una ruta contiene `..`;
- falta algún archivo esencial.

Archivos esenciales mínimos:

- `app/`;
- `alembic/` y las revisiones `001` y `002`;
- `tests/`;
- `frontend/`;
- `requirements.txt`;
- `README.md`;
- `.env.example`;
- `.gitignore`;
- `alembic.ini`;
- documentos de fase y resultados.

El ZIP final no debe contener `venv`, aunque el entorno continúe existiendo en la carpeta de trabajo.

---

## 7. Pruebas y criterios de aceptación

La Fase 2.2 se aprueba solamente si:

- `pip install -r requirements.txt` funciona sin modificaciones temporales.
- `pip check` no reporta conflictos.
- Se conservan las 45 pruebas actuales.
- Se agregan pruebas reales de los tres escenarios de migración.
- Toda la suite pasa dos veces consecutivas.
- Una base nueva migrada permite usar proyectos, casos, suites, asociaciones, ejecuciones e historial.
- Ninguna operación anterior responde 500.
- `alembic current` muestra `002_phase2_schema_alignment (head)` o el nombre equivalente definido.
- `PRAGMA foreign_key_check` está vacío en los tres escenarios.
- El esquema migrado coincide con los modelos SQLAlchemy.
- CORS no usa wildcard con credenciales.
- El README describe el estado real.
- El ZIP final no incluye ninguna exclusión y utiliza `/` en todas sus rutas.

Ejecuta obligatoriamente:

```bash
python -m pip install -r requirements.txt
python -m pip check
python -m pytest -q
python -m pytest -q
alembic history
alembic current
```

---

## 8. Entregables

Entrega:

1. `Fase_2_2_Limpio.zip`.
2. `RESULTADO_FASE_2_2.md`.

El informe debe incluir:

- archivos modificados;
- corrección de codificación de `requirements.txt`;
- migración `002` creada;
- resultado real de los tres escenarios;
- revisión `head` obtenida;
- comparación automática de esquema y modelos;
- total exacto de pruebas completas y dos ejecuciones;
- evidencia funcional de la API sobre una base nueva migrada;
- configuración CORS final;
- cantidad de entradas del ZIP;
- confirmación de cero rutas con `\` y cero archivos excluidos;
- pendientes reales para la Fase 3.

No declares la fase completada si la instalación oficial falla, la base nueva responde 500 o el ZIP contiene un entorno virtual.

---

## 9. Instrucción final para Antigravity

Corrige únicamente los errores de cierre descritos. No reescribas el motor SQL, no elimines pruebas, no desarrolles todavía el frontend integral y no despliegues. Al finalizar, genera el informe y el ZIP limpio, y verifica ambos antes de entregarlos.
