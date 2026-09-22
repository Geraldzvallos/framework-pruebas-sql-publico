# FASE 3 — Frontend completo e integración de extremo a extremo

## Framework de pruebas de base de datos SQL

Coloca este archivo en la **raíz de la copia más reciente del proyecto**, junto a `AGENTS.md`, `README.md` y `RESULTADO_FASE_2_2.md`.

Esta instrucción constituye la aprobación expresa para ejecutar íntegramente la Fase 3. Presenta primero un plan corto, pero **no te detengas esperando otra aprobación**: continúa con la implementación, las pruebas, la verificación en navegador y el empaquetado final.

No despliegues todavía. El despliegue corresponde a una fase posterior, una vez que esta interfaz haya sido revisada externamente.

---

## 1. Instrucción principal para el agente

Lee completamente, antes de modificar archivos:

1. `AGENTS.md`;
2. `README.md`;
3. `FASE_2_MODELO_API_Y_TRAZABILIDAD.md`;
4. `FASE_2_1_CORRECCION_Y_CIERRE.md`;
5. `FASE_2_2_CORRECCION_FINAL.md`;
6. `RESULTADO_FASE_2.md`;
7. `RESULTADO_FASE_2_1.md`;
8. `RESULTADO_FASE_2_2.md`;
9. este documento;
10. todos los archivos del backend, frontend, pruebas y migraciones que sean relevantes.

Después:

- comprueba el estado inicial ejecutando migraciones, pruebas y aplicación;
- revisa el contrato real de `/openapi.json` y usa esos endpoints y esquemas como fuente de verdad;
- presenta un plan breve de implementación;
- ejecuta toda la fase sin limitarte a redactar otro plan;
- verifica cada flujo de forma reproducible;
- genera el informe y el ZIP limpio solicitados al final.

Si encuentras una diferencia entre un documento antiguo y el código validado de la Fase 2.2, conserva el comportamiento probado por el código y documenta la diferencia. No inventes endpoints ni campos.

---

## 2. Estado inicial ya verificado externamente

La Fase 2.2 fue revisada fuera del agente y se confirmó lo siguiente:

- instalación correcta desde `requirements.txt` en un entorno nuevo;
- `pip check` sin dependencias rotas;
- migración vigente `002`;
- ZIP limpio y portable;
- **48 pruebas aprobadas dos veces consecutivas**;
- backend, API, migraciones y aislamiento de pruebas estables;
- funcionamiento básico de proyectos, perfiles, casos, suites, ejecución e historial comprobado mediante la API.

El frontend actual sigue incompleto:

- solo lista, crea y elimina casos de prueba;
- solo lista suites;
- el botón de suite muestra “Motor en Espera” y no ejecuta la API;
- no ofrece gestión completa de proyectos;
- no ofrece gestión de perfiles Oracle ni prueba de conexión;
- no permite asociar o retirar casos de una suite;
- no ejecuta casos individuales;
- no muestra el historial completo ni sus filtros;
- varios indicadores están fijos o no representan datos reales;
- `API_URL` está fijada a `http://127.0.0.1:8000/api`, lo cual no es apto para despliegue;
- se insertan datos devueltos por la API mediante `innerHTML`, con riesgo de inyección en la interfaz.

La finalidad de esta fase es cerrar esas brechas **sin reescribir ni desestabilizar el backend aprobado**.

---

## 3. Alcance obligatorio

### 3.1 Tecnologías que se deben conservar

- Python y FastAPI en el backend.
- SQLAlchemy y SQLite para la información interna.
- Oracle mediante `oracledb` como base objetivo del MVP.
- HTML, CSS, JavaScript y Bootstrap 5 en el frontend.
- Pytest para pruebas.

No convertir el frontend a React, Angular, Vue, TypeScript ni otro framework. No introducir JPA, PHP, Supabase ni una base diferente. Mantén la solución sencilla y entendible para estudiantes.

### 3.2 Integración del frontend con la misma aplicación

Sirve el frontend desde FastAPI en una ruta estable, preferentemente:

```text
/ui/
```

La ruta raíz `/` puede seguir funcionando como comprobación de salud del backend. `/docs` y `/openapi.json` deben continuar disponibles.

Requisitos:

- usar `StaticFiles` o una solución equivalente simple de FastAPI;
- las rutas de recursos deben funcionar tanto localmente como después del despliegue;
- cuando la interfaz se sirva desde FastAPI, debe consumir `/api` en el mismo origen;
- eliminar la dependencia obligatoria de una URL fija a `127.0.0.1`;
- permitir una configuración explícita de URL únicamente como alternativa documentada para desarrollo separado;
- no abrir `index.html` con `file://` como procedimiento oficial;
- documentar que el acceso normal será `http://127.0.0.1:8000/ui/` durante el desarrollo.

### 3.3 Estado general y navegación

La interfaz debe incluir, como mínimo, secciones claras para:

1. Proyectos.
2. Perfiles de conexión Oracle.
3. Casos de prueba.
4. Suites.
5. Ejecución.
6. Historial.
7. Ayuda o instrucciones de uso breves.

También debe:

- mostrar si la API está disponible consultando realmente el backend;
- mostrar el proyecto activo y permitir cambiarlo;
- filtrar perfiles, casos, suites e historial según el proyecto activo cuando corresponda;
- funcionar en pantalla de escritorio y adaptarse razonablemente a móvil;
- presentar estados de carga, listas vacías y errores comprensibles;
- evitar botones que no hagan nada o textos “Pronto” para funciones del MVP.

No agregues autenticación, roles, inteligencia artificial, auditoría avanzada, gráficas complejas ni reportes PDF en esta fase.

---

## 4. Flujos funcionales obligatorios

### 4.1 Proyectos

Conecta el CRUD existente de `/api/projects/`:

- listar proyectos;
- crear proyecto;
- ver o cargar sus datos;
- editar nombre y descripción;
- eliminar únicamente cuando el backend lo permita;
- mostrar claramente el mensaje `409` cuando tenga dependencias;
- actualizar el selector de proyecto activo después de crear, editar o eliminar.

No ocultes las validaciones del backend ni simules eliminaciones exitosas.

### 4.2 Perfiles de conexión Oracle

Conecta el CRUD de `/api/connections/`:

- listar por proyecto;
- crear perfil con nombre, motor permitido, host, puerto, service name y usuario;
- editar el perfil;
- eliminar el perfil;
- probar la conexión mediante `/api/connections/{id}/test`.

Reglas de seguridad:

- solicitar la contraseña solo al probar o ejecutar;
- nunca guardarla en `localStorage`, `sessionStorage`, cookies, HTML, URL ni perfil;
- no mostrarla nuevamente en pantalla;
- limpiar el campo después de utilizarlo;
- no imprimirla en consola ni incluirla en mensajes de error;
- no afirmar “conexión exitosa” si Oracle no respondió realmente.

Si no existe un servidor Oracle disponible, la interfaz debe manejar el error real de forma clara. Las pruebas automáticas pueden usar mocks, pero el informe debe diferenciar explícitamente una prueba simulada de una prueba contra Oracle real.

### 4.3 Casos de prueba

Completa el CRUD de `/api/test-cases/`:

- listar por proyecto;
- crear;
- editar;
- eliminar con confirmación;
- ver el SQL completo sin dañar la tabla o el diseño;
- seleccionar `validation_type` entre `ROW_COUNT` y `EXISTS`;
- adaptar la ayuda y validación de `expected_result`:
  - `ROW_COUNT`: entero igual o mayor que cero;
  - `EXISTS`: valor booleano permitido por el esquema real;
- mostrar los mensajes `422`, `404` y `409` devueltos por la API.

No permitir que el frontend convierta silenciosamente un caso de un proyecto en un caso de otro proyecto.

### 4.4 Suites

Conecta todos los endpoints reales de suites:

- listar suites del proyecto activo;
- crear, editar y eliminar suites;
- ver el detalle de una suite;
- mostrar casos asociados;
- asociar casos disponibles del mismo proyecto;
- retirar casos de la suite;
- impedir duplicados y mostrar el `409` real;
- no permitir asociaciones entre proyectos diferentes;
- actualizar la pantalla inmediatamente después de cada cambio confirmado.

### 4.5 Ejecución individual y por suite

Conecta:

```text
POST /api/execute/test-case/{test_case_id}
POST /api/execute/suite/{suite_id}
```

La interfaz debe permitir:

- elegir el caso o suite;
- elegir un perfil de conexión perteneciente al mismo proyecto;
- ingresar la contraseña solo para esa operación;
- confirmar antes de iniciar;
- bloquear temporalmente el botón para evitar doble envío;
- mostrar progreso;
- presentar `PASS`, `FAIL` o `ERROR` con texto además del color;
- en suites, mostrar total, aprobadas, fallidas, errores, duración y detalle por caso;
- explicar si se aplicó `rollback` cuando corresponda;
- limpiar la contraseña al terminar, incluso si ocurre un error;
- recargar el historial después de una ejecución.

No ejecutes SQL destructivo de demostración contra una base real. Respeta el validador actual y las restricciones de `AGENTS.md`.

El endpoint `/api/execute/raw` puede incluirse únicamente como herramienta secundaria y controlada si ya encaja limpiamente en la interfaz. No debe sustituir la ejecución de casos y suites, que es el flujo principal.

### 4.6 Historial y evidencia

Conecta `/api/history/` y `/api/history/{id}`:

- listar del más reciente al más antiguo;
- filtrar por proyecto, caso, suite y estado;
- ofrecer estados `PASS`, `FAIL` y `ERROR`;
- respetar `skip` y `limit` o implementar paginación sencilla;
- abrir el detalle de un registro;
- mostrar, cuando existan: SQL ejecutado, tipo de sentencia, validación, esperado, obtenido, filas, duración, rollback y error;
- no mostrar contraseñas ni secretos;
- diferenciar lista vacía de error de conexión.

### 4.7 Indicadores reales

Sustituye valores fijos por valores calculados a partir de respuestas reales:

- total de casos del proyecto activo;
- total de suites del proyecto activo;
- total de perfiles del proyecto activo;
- resumen de ejecuciones disponibles en el historial, como PASS/FAIL/ERROR.

No inventes porcentajes ni cifras. Si un indicador no puede calcularse con los endpoints actuales, elimínalo o sustitúyelo por uno verificable.

---

## 5. Calidad y seguridad del frontend

Implementa una función central para peticiones HTTP que:

- compruebe `response.ok`;
- intente obtener `detail` de FastAPI;
- maneje respuestas sin cuerpo, especialmente `204`;
- diferencie errores de validación, conflictos, no encontrados y falta de conexión;
- evite repetir lógica en cada pantalla.

Además:

- no insertes datos no confiables mediante plantillas `innerHTML`;
- crea nodos y asigna texto mediante `textContent`, o aplica un escape seguro y comprobado;
- elimina `onclick` construidos con datos provenientes de la API;
- valida formularios también en el frontend, sin reemplazar la validación del backend;
- usa etiquetas, ayudas y mensajes comprensibles en español;
- conserva accesibilidad básica: `label`, foco visible, botones identificables y mensajes que no dependan solo del color;
- no registres secretos en consola;
- evita recargas completas de la página para operaciones normales;
- conserva el código modular. Puedes separar `app.js` en varios archivos si mejora claramente el mantenimiento, sin introducir un sistema de compilación innecesario.

---

## 6. Pruebas obligatorias

### 6.1 Regresión del backend

Antes y después de implementar:

```bash
alembic upgrade head
pytest -q
pytest -q
```

Las **48 pruebas existentes deben seguir pasando**. No elimines, marques como `skip`, relajes ni modifiques pruebas solo para obtener un resultado verde.

### 6.2 Pruebas nuevas de Fase 3

Agrega pruebas automatizadas reproducibles para, como mínimo:

- `/ui/` responde `200` y devuelve el HTML del frontend;
- los recursos JavaScript/CSS locales necesarios responden correctamente;
- `/`, `/docs` y `/openapi.json` continúan disponibles;
- la configuración de API del frontend funciona con el mismo origen y no depende obligatoriamente de `127.0.0.1`;
- existen los controles principales de proyectos, conexiones, casos, suites, ejecución e historial;
- el backend conserva el manejo de los contratos usados por la interfaz;
- las contraseñas no aparecen en respuestas, HTML, archivos generados ni registros de prueba.

Si el entorno permite pruebas reales de navegador, añade y ejecuta un recorrido automatizado. Si no lo permite, no finjas que se ejecutó: realiza la verificación manual de navegador descrita abajo y documenta la limitación.

### 6.3 Verificación manual real en navegador

Inicia el proyecto con una base interna temporal o limpia:

```bash
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abre `/ui/` y verifica, en este orden:

1. Estado real del backend.
2. Crear y seleccionar un proyecto.
3. Crear y editar un perfil Oracle sin almacenar contraseña.
4. Crear un caso `ROW_COUNT`.
5. Crear un caso `EXISTS`.
6. Editar y eliminar un caso de prueba creado para verificación.
7. Crear una suite.
8. Asociar y retirar un caso.
9. Volver a asociarlo.
10. Abrir el flujo de ejecución individual.
11. Abrir el flujo de ejecución de suite.
12. Consultar y filtrar el historial.
13. Recargar la página y comprobar que los datos internos persisten.
14. Probar un formulario inválido y comprobar que el error sea comprensible.
15. Comprobar que no aparezcan errores JavaScript en la consola.

Para las ejecuciones Oracle:

- si hay una instancia real de pruebas, utiliza solamente credenciales proporcionadas mediante variables o entrada temporal y documenta el resultado sin revelar secretos;
- si no la hay, valida el flujo mediante mocks en pruebas y verifica manualmente que la interfaz muestre correctamente el error real de conexión;
- no cambies el producto para simular un éxito engañoso en la interfaz.

---

## 7. Documentación de uso

Actualiza `README.md` con instrucciones exactas para Windows PowerShell y, de forma breve, Linux/macOS:

1. crear y activar entorno virtual;
2. instalar `requirements.txt`;
3. copiar `.env.example` a `.env`;
4. aplicar `alembic upgrade head`;
5. iniciar Uvicorn;
6. abrir `/ui/`;
7. crear proyecto;
8. configurar perfil Oracle;
9. crear casos y suites;
10. ejecutar y revisar historial;
11. ejecutar pruebas automáticas.

Incluye una sección “Limitaciones reales” que indique:

- si Oracle real fue o no probado;
- que nunca se debe usar una base de producción;
- que el despliegue todavía no forma parte de la Fase 3;
- cualquier función que permanezca pendiente, sin afirmaciones exageradas.

Actualiza `.env.example` únicamente con variables realmente utilizadas y valores de ejemplo no secretos.

---

## 8. Prohibiciones de esta fase

- No desplegar a servicios externos.
- No modificar ni borrar el historial de migraciones `001` y `002`.
- No recrear la base con `Base.metadata.create_all()` durante el arranque.
- No publicar `framework_interno.db`.
- No incluir `.env`, contraseñas, tokens ni credenciales en archivos o ZIP.
- No sustituir el backend aprobado por otro.
- No alterar la lógica del motor de ejecución salvo que exista un error reproducible indispensable para integrar la interfaz; si ocurre, aplica una corrección mínima con prueba y explicación.
- No afirmar que Oracle real fue validado si solo se utilizaron mocks.
- No añadir funciones fuera del MVP para aparentar mayor avance.
- No reducir las pruebas existentes.

---

## 9. Criterios de aceptación

La Fase 3 se considera terminada únicamente si se cumplen todos estos puntos:

- [ ] El proyecto se instala desde cero sin dependencias manuales adicionales.
- [ ] `alembic upgrade head` termina correctamente.
- [ ] Las 48 pruebas anteriores continúan aprobadas.
- [ ] Las nuevas pruebas de frontend/integración están incluidas y aprobadas.
- [ ] La suite completa pasa dos veces consecutivas.
- [ ] FastAPI inicia sin errores.
- [ ] `/`, `/docs`, `/openapi.json` y `/ui/` funcionan.
- [ ] Se puede gestionar proyectos desde la interfaz.
- [ ] Se puede gestionar perfiles y probar una conexión desde la interfaz.
- [ ] Se puede crear, editar y eliminar casos.
- [ ] Se puede gestionar suites y sus asociaciones.
- [ ] La ejecución individual está conectada.
- [ ] La ejecución de suites está conectada.
- [ ] El historial y sus filtros funcionan.
- [ ] Los indicadores muestran datos reales.
- [ ] Los errores `404`, `409`, `422` y de conexión se muestran correctamente.
- [ ] Las contraseñas no se persisten ni se exponen.
- [ ] No existen errores JavaScript durante el recorrido principal.
- [ ] El README permite que otra persona instale y use el proyecto.
- [ ] El ZIP final es limpio, portable y no contiene secretos ni bases locales.

Si un punto no puede cumplirse, no declares la fase completa. Documenta el bloqueo exacto y entrega la evidencia disponible.

---

## 10. Entregables obligatorios

### 10.1 Informe

Crea en la raíz:

```text
RESULTADO_FASE_3.md
```

Debe contener:

1. resumen real de lo implementado;
2. archivos creados y modificados;
3. decisiones de integración frontend/backend;
4. tabla de endpoints consumidos por cada pantalla;
5. comandos ejecutados;
6. resultado completo de `pip check`, migraciones y pruebas;
7. resultado de las dos ejecuciones finales de la suite;
8. recorrido manual realizado y su resultado paso a paso;
9. evidencia de prueba con mocks y, por separado, estado de Oracle real;
10. errores encontrados y cómo fueron corregidos;
11. limitaciones o pendientes reales;
12. instrucciones para iniciar y usar el sistema;
13. recomendación para la Fase 4 de preparación de despliegue.

No escribas “todo funciona” sin resultados verificables.

### 10.2 ZIP limpio

Actualiza o reutiliza de forma segura `scripts/build_clean_zip.py` y genera:

```text
Fase_3_Limpio.zip
```

Debe incluir el código, migraciones, frontend, pruebas, documentación y `RESULTADO_FASE_3.md`.

Debe excluir:

- `venv/`, `.venv/` y cualquier entorno virtual;
- `.pytest_cache/` y `__pycache__/`;
- compilados Python;
- `.env` y cualquier secreto;
- archivos `.db`, `.sqlite` y `.sqlite3`;
- logs, cobertura y temporales;
- ZIP anteriores;
- metadatos innecesarios del sistema o IDE.

Valida después de crearlo que:

- todas las rutas usan `/`;
- no existen rutas absolutas ni `..`;
- no falta ningún archivo esencial;
- el propio ZIP no está contenido dentro de sí mismo;
- `RESULTADO_FASE_3.md` está incluido.

---

## 11. Respuesta final esperada del agente

Al terminar, responde de forma concreta con:

1. si la Fase 3 fue completada o quedó bloqueada;
2. total exacto de pruebas aprobadas y duración;
3. confirmación de dos ejecuciones completas;
4. URL local exacta para abrir la interfaz;
5. flujo breve para usarla;
6. estado de la prueba Oracle: real, simulada o no disponible;
7. pendientes reales;
8. ubicación de `RESULTADO_FASE_3.md`;
9. ubicación de `Fase_3_Limpio.zip`.

No avances a despliegue hasta que el ZIP de esta fase sea revisado externamente.

---

## Texto corto para pegar en el chat del agente

```text
Lee completamente AGENTS.md, README.md, los documentos y resultados de las Fases 2, 2.1 y 2.2, y FASE_3_FRONTEND_INTEGRACION_E2E.md. Ejecuta íntegramente la Fase 3 sobre el proyecto actual. Este documento ya autoriza la implementación: presenta un plan breve y continúa sin esperar otra aprobación. No te limites a analizar ni a redactar otro plan. Conserva el backend y las 48 pruebas existentes, conecta y completa el frontend con la API real, verifica todos los flujos, agrega pruebas reproducibles, ejecuta la suite completa dos veces y genera RESULTADO_FASE_3.md y Fase_3_Limpio.zip. No despliegues todavía y no afirmes que Oracle real funciona si solo utilizaste mocks.
```
