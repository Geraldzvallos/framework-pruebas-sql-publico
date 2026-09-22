# FASE 3.1 — Corrección y cierre real del frontend

## Framework de pruebas de base de datos SQL

Coloca este archivo en la raíz del proyecto que produjo `Fase_3_Limpio.zip`. Esta instrucción autoriza únicamente las correcciones de la Fase 3 descritas aquí. No despliegues todavía y no modifiques la lógica estable del motor, las migraciones `001`/`002` ni las 48 pruebas anteriores.

Presenta un plan corto y luego continúa con toda la implementación sin esperar una segunda aprobación. No te limites a redactar otro plan.

---

## 1. Resultado de la auditoría externa

La entrega tiene elementos correctos:

- el ZIP contiene 62 entradas y está limpio;
- no contiene entornos virtuales, cachés, bases locales, secretos ni rutas inseguras;
- `pip check` no informa dependencias rotas;
- `alembic upgrade head` funciona;
- Uvicorn inicia correctamente;
- `/`, `/docs`, `/openapi.json`, `/ui/` y `/ui/app.js` responden `200`;
- `node --check frontend/app.js` no detecta errores de sintaxis;
- las 54 pruebas pasan dos veces: `54 passed in 3.53s` y `54 passed in 3.41s`.

Sin embargo, la Fase 3 **no está aprobada funcionalmente**. Las seis pruebas nuevas son comprobaciones estáticas y de disponibilidad; no ejecutan el comportamiento del navegador ni validan los cuerpos JSON construidos por el frontend. La auditoría reprodujo los errores que siguen.

---

## 2. Error crítico: perfiles de conexión incompatibles con la API

`frontend/app.js` utiliza:

```javascript
profile_name
sid
```

El contrato real de `ConnectionProfileCreate` y `ConnectionProfileResponse` utiliza:

```text
name
service_name
```

`service_name` es obligatorio y el backend no tiene el campo `sid`.

La auditoría ejecutó exactamente el cuerpo construido por el frontend y obtuvo:

```text
POST /api/connections/ -> 422
Campo faltante: body.name
```

Por lo tanto, actualmente no se puede crear correctamente un perfil desde la interfaz y los perfiles existentes aparecen sin nombre.

### Corrección obligatoria

- Sustituye `profile_name` por `name` al crear, listar y seleccionar perfiles.
- Elimina `sid` del formulario y del cuerpo JSON.
- Haz que `service_name` sea obligatorio en el formulario.
- Envía `engine: "ORACLE"`.
- Verifica que el JSON construido por la interfaz coincida exactamente con el esquema OpenAPI.
- Añade una prueba que envíe exactamente el cuerpo usado por el frontend y compruebe `201`.
- Comprueba también listar, editar, probar y eliminar el perfil.

---

## 3. Error crítico: respuesta de ejecución de suites mal interpretada

La API real devuelve directamente:

```text
suite_id
suite_name
total_tests
passed
failed
errors
total_duration_ms
details
```

El frontend intenta leer propiedades inexistentes:

```javascript
res.summary
res.results
summary.total_executed
summary.total_passed
summary.total_failed
summary.total_errors
```

La auditoría ejecutó una suite mediante la API y comprobó que la respuesta `200` contiene las claves reales indicadas arriba. En el navegador, `res.results.forEach(...)` produce un error porque `results` no existe.

### Corrección obligatoria

Usa el contrato real:

```javascript
res.total_tests
res.passed
res.failed
res.errors
res.total_duration_ms
res.details
```

La ventana de resultado debe mostrar el resumen y recorrer `res.details`. Debe funcionar con:

- suite con casos;
- suite vacía;
- resultados PASS;
- resultados FAIL;
- resultados ERROR;
- error HTTP del backend.

Añade una prueba reproducible con el ejecutor Oracle simulado que valide la misma estructura consumida por la interfaz.

---

## 4. Casos disponibles para asociar a suites

`actualizarKPIsProyecto()` descarga los casos pero no asigna el resultado a `estado.casos`. Si el usuario abre Suites antes de abrir Casos de Prueba, el selector para asociar casos queda vacío.

### Corrección obligatoria

- Asigna siempre `estado.casos = casos` al cargar el proyecto activo, o carga explícitamente los casos antes de renderizar suites.
- Excluye del selector los casos que ya pertenecen a la suite.
- Después de asociar o retirar, actualiza el estado y la interfaz.
- Prueba el flujo entrando directamente a Suites sin visitar antes la sección de Casos.

---

## 5. CRUD incompleto

La interfaz solamente permite crear y eliminar. No existen llamadas `PUT`, botones de edición ni formularios precargados para:

- proyectos;
- perfiles de conexión;
- casos de prueba;
- suites.

Esto contradice el alcance aprobado y el informe, que declara gestión integral.

### Corrección obligatoria

Implementa y verifica:

```text
PUT /api/projects/{project_id}
PUT /api/connections/{connection_id}
PUT /api/test-cases/{test_case_id}
PUT /api/suites/{suite_id}
```

Cada listado debe incluir una acción Editar. Los formularios deben:

- mostrar los datos actuales;
- enviar únicamente campos válidos;
- conservar el `project_id` original cuando corresponda;
- mostrar errores `404`, `409` y `422` de forma comprensible;
- actualizar la interfaz después de guardar;
- no almacenar contraseñas.

No bloquees la eliminación del proyecto ID 1 mediante una regla inventada en JavaScript. Solicita confirmación y deja que el backend determine si puede eliminarse según sus dependencias.

---

## 6. Validación y errores de formularios

La respuesta `422` de FastAPI suele incluir `detail` como una lista de objetos. La función actual puede mostrar `[object Object]` en lugar de un mensaje entendible.

### Corrección obligatoria

- Normaliza `detail` cuando sea texto, lista o estructura anidada.
- Muestra nombre de campo y mensaje de validación.
- Diferencia al menos `404`, `409`, `422` y error de red.
- Sustituye los `console.error` silenciosos por un estado visible para el usuario, sin exponer secretos.
- Para `ROW_COUNT`, valida un entero `>= 0`.
- Para `EXISTS`, limita la selección a `true` o `false`.
- Cambia la ayuda del resultado esperado al cambiar `validation_type`.
- Desactiva Guardar mientras la petición está en progreso para evitar doble envío.

---

## 7. Funciones y secciones faltantes

Completa estos puntos exigidos en la Fase 3:

### 7.1 Ver SQL completo

El SQL aparece truncado y no existe acción para consultarlo completo. Agrega una vista segura de detalle usando `textContent` o escape correcto.

### 7.2 Ejecución

Mantén los botones de ejecución en Casos y Suites, pero agrega una sección clara de Ejecución o una pantalla equivalente que permita comprender:

- qué proyecto está activo;
- qué caso o suite se ejecutará;
- qué perfil se utilizará;
- que la contraseña es temporal;
- el resultado PASS, FAIL o ERROR;
- el rollback aplicado;
- el enlace o acceso al historial generado.

### 7.3 Historial

Agrega filtros reales por:

- proyecto;
- caso (`test_case_id`);
- suite (`suite_id`);
- estado.

Agrega paginación sencilla usando `skip` y `limit`, con botones Anterior/Siguiente y estado de página. El detalle debe mostrar también duración, rollback, error de rollback y mensaje de error cuando existan.

### 7.4 Ayuda

Agrega una sección breve de Ayuda que explique el flujo:

```text
Proyecto → Perfil Oracle → Casos → Suite → Ejecución → Historial
```

Incluye la advertencia de no usar una base Oracle de producción.

### 7.5 Indicadores

Conserva casos, suites y perfiles del proyecto activo. Sustituye “Total Proyectos” o añade un resumen del historial con cifras reales de PASS, FAIL y ERROR. No inventes porcentajes.

### 7.6 Navegación móvil

La barra lateral actual desaparece en pantallas pequeñas y no existe reemplazo. Agrega una barra o menú `offcanvas` de Bootstrap para acceder a todas las secciones desde móvil.

---

## 8. Seguridad y construcción del DOM

La Fase 3 pidió no construir manejadores `onclick` con datos devueltos por la API. La entrega todavía genera muchos `onclick="...(${id})"` dentro de `innerHTML`.

### Corrección obligatoria

- Crea botones mediante DOM o usa atributos `data-*` con listeners registrados desde JavaScript.
- Usa `textContent` para valores provenientes de la API.
- Reserva `innerHTML` únicamente para fragmentos estáticos controlados.
- No insertes mensajes del backend, SQL, resultados ni nombres como HTML sin escape.
- No registres contraseñas en consola.
- Limpia la contraseña en `finally`, tanto en éxito como en error.
- Confirma mediante una prueba o revisión que no se use `localStorage`, `sessionStorage`, cookies o parámetros URL para credenciales.

---

## 9. Archivo generador no portable

`scripts/generate_frontend.py` contiene esta ruta absoluta de otra computadora:

```text
c:\Users\MSI\Downloads\framework-pruebas-sql-main\framework-pruebas-sql-main
```

El script no es portable y podría sobrescribir el frontend corregido con la versión defectuosa.

### Corrección obligatoria

Elige una de estas opciones:

1. elimina `scripts/generate_frontend.py` porque no es necesario para ejecutar el proyecto; o
2. refactorízalo para usar rutas relativas a `Path(__file__).resolve().parent.parent`, sin código frontend duplicado ni rutas personales.

La opción recomendada es eliminarlo si solo fue una herramienta temporal.

Verifica que no quede ninguna ruta `C:\Users\...` o ruta personal en el proyecto.

---

## 10. README e informe incorrectos

`README.md` no fue actualizado. Todavía afirma:

- frontend limitado;
- pantallas pendientes para Fase 3;
- suite en “Motor en Espera”;
- total de 48 pruebas.

`RESULTADO_FASE_3.md` afirma que la gestión es integral y que el recorrido manual fue exitoso, aunque existen los errores reproducibles anteriores. También denomina “E2E” a pruebas que no ejecutan el navegador.

### Corrección obligatoria

- Actualiza `README.md` con el estado final verdadero, `/ui/`, instalación y uso en Windows PowerShell y Linux/macOS.
- Actualiza el total real de pruebas después de agregar las nuevas.
- Explica que Oracle real sigue pendiente si solo se usaron mocks.
- Corrige `RESULTADO_FASE_3.md` o crea `RESULTADO_FASE_3_1.md` con evidencia exacta.
- No declares pruebas E2E de navegador si no se ejecutaron realmente.
- Elimina como pendientes PDF, CSV, autenticación, roles o multi-motor: están fuera del MVP y no son bloqueos de despliegue.
- No recomiendes Postgres/MySQL para esta etapa; Oracle es el motor objetivo definido en `AGENTS.md`.

---

## 11. Pruebas obligatorias para cerrar la fase

Mantén las 54 pruebas actuales y agrega cobertura que detecte los defectos anteriores.

### 11.1 Validaciones automáticas mínimas

1. La carga de un perfil usa `name`, no `profile_name`, y el cuerpo exacto responde `201`.
2. El frontend no contiene referencias a `profile_name` ni al campo `sid`.
3. La respuesta de suite se procesa con `total_tests`, `passed`, `failed`, `errors` y `details`.
4. No existen referencias a `res.summary`, `res.results`, `total_executed`, `total_passed`, `total_failed` o `total_errors`.
5. Existen flujos `PUT` para proyectos, perfiles, casos y suites.
6. Las asociaciones funcionan aunque el usuario no haya abierto antes la pantalla de casos.
7. Los filtros de historial construyen correctamente `test_case_id`, `suite_id`, `status`, `skip` y `limit`.
8. Un `422` se transforma en un mensaje legible.
9. El menú móvil permite entrar a todas las secciones.
10. No hay credenciales ni rutas personales en el código.
11. `node --check frontend/app.js` termina con código 0. Si separas el código, valida todos los archivos JavaScript propios.

No conviertas simples búsquedas de texto en la única evidencia. Prueba también los endpoints con los mismos cuerpos usados por el frontend.

### 11.2 Recorrido real en navegador

Inicia el servidor y realiza el recorrido desde `/ui/`:

1. crear y editar proyecto;
2. crear, listar y editar perfil Oracle;
3. probar conexión y comprobar manejo del error real si no existe Oracle;
4. crear y editar casos `ROW_COUNT` y `EXISTS`;
5. ver SQL completo;
6. crear y editar suite;
7. entrar directamente a Suites y asociar un caso;
8. retirar y volver a asociar;
9. ejecutar un caso con Oracle simulado en prueba automatizada;
10. ejecutar una suite con Oracle simulado y mostrar el resumen correcto;
11. consultar detalle del historial;
12. probar todos los filtros y la paginación;
13. eliminar datos de verificación respetando dependencias;
14. revisar móvil o ancho reducido;
15. confirmar que la consola no tenga errores JavaScript.

Si el navegador del entorno no permite mockear Oracle desde la interfaz, no simules un éxito visual falso. Valida la ejecución mediante una prueba automatizada del contrato y verifica en navegador el manejo del error de conexión.

Guarda evidencias sin contraseñas en `evidencias/fase_3_1/` o documenta exactamente qué herramienta y pasos se utilizaron. No afirmes que se hizo el recorrido si no se realizó.

### 11.3 Comandos finales

Ejecuta en un entorno limpio:

```bash
python -m venv .venv-audit
python -m pip install -r requirements.txt
python -m pip check
alembic upgrade head
node --check frontend/app.js
pytest -q
pytest -q
```

Después inicia Uvicorn y comprueba respuestas `200` de:

```text
/
/docs
/openapi.json
/ui/
/ui/app.js
```

No elimines, relajes, omitas ni marques pruebas como `skip`.

---

## 12. Entregables

Crea:

```text
RESULTADO_FASE_3_1.md
Fase_3_1_Limpio.zip
```

El informe debe incluir:

- errores reproducidos antes de corregir;
- archivos modificados;
- tabla del contrato frontend/API corregido;
- operaciones CRUD verificadas;
- resultado real de ejecución individual y suite con mocks;
- estado separado de Oracle real;
- comandos y resultados completos;
- total exacto de pruebas;
- dos ejecuciones consecutivas;
- recorrido de navegador y evidencias;
- limitaciones reales restantes;
- URL local e instrucciones de uso.

El ZIP debe incluir el informe, código, pruebas y documentación, y excluir entornos, cachés, `.env`, bases, logs, credenciales, ZIP anteriores y rutas personales. Valídalo después de crearlo.

---

## 13. Criterio de cierre

No declares la Fase 3.1 completa si cualquiera de estos puntos falla:

- creación de perfil desde la interfaz;
- listado correcto del nombre del perfil;
- edición de los cuatro recursos;
- asociación de casos al entrar directamente a Suites;
- ejecución y resumen de suite con el contrato real;
- filtros y paginación del historial;
- navegación móvil;
- README actualizado;
- pruebas completas dos veces;
- recorrido real sin errores JavaScript.

No despliegues. La revisión externa del nuevo ZIP decidirá si se puede pasar a la Fase 4.

---

## Texto corto para pegar en Antigravity

```text
Lee completamente AGENTS.md, FASE_3_FRONTEND_INTEGRACION_E2E.md, RESULTADO_FASE_3.md y FASE_3_1_CORRECCION_Y_CIERRE.md. Ejecuta íntegramente la Fase 3.1 sobre el proyecto actual. Este documento ya autoriza estas correcciones: presenta un plan breve y continúa sin esperar otra aprobación. Reproduce y corrige los contratos rotos de perfiles y ejecución de suites, completa los CRUD y funciones faltantes, mejora las pruebas para que detecten fallos reales del frontend, realiza el recorrido de navegador, actualiza README e informe y genera RESULTADO_FASE_3_1.md y Fase_3_1_Limpio.zip. Conserva el backend, migraciones y pruebas anteriores. No despliegues todavía.
```
