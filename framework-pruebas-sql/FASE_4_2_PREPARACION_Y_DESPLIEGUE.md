# FASE 4.2 — PREPARACIÓN DE PRODUCCIÓN Y DESPLIEGUE

## Framework de pruebas de base de datos SQL

**Fecha de inicio:** 21 de septiembre de 2026  
**Línea base autorizada:** Fase 4.1.1 aprobada  
**Objetivo de esta instrucción:** dejar el proyecto actual listo para un despliegue reproducible y, si se proporcionan servidor, dominio y credenciales, realizar el despliegue público sin alterar el alcance funcional aprobado.

---

## Instrucción principal para Antigravity

Lee completamente, antes de modificar cualquier archivo:

1. `AGENTS.md`.
2. `README.md`.
3. `PLAN_REVISION_FRAMEWORK_PRUEBAS_SQL.md`.
4. `FASE_4_1_ORACLE_REAL.md`.
5. `FASE_4_1_1_CORRECCION_FINAL.md`.
6. `RESULTADO_FASE_4_1_CORREGIDA.md`.
7. Este archivo.

Trabaja **únicamente sobre la carpeta actual del proyecto**. No crees otro proyecto, no dupliques el repositorio y no borres el historial, las migraciones, las pruebas ni los documentos existentes.

Presenta un plan breve y continúa sin esperar otra aprobación. Solo debes detener la parte externa del despliegue cuando falte realmente alguno de estos elementos:

- servidor o proveedor elegido;
- dominio o URL definitiva;
- acceso SSH o mecanismo equivalente;
- secretos requeridos por el servidor;
- aceptación de términos o inicio de sesión en el registro oficial de Oracle.

Aunque exista uno de esos bloqueos, debes completar y validar toda la preparación local de producción. Nunca inventes que una URL, un workflow, una conexión o una prueba funcionó.

---

## 1. Línea base que debe conservarse

Antes de cambiar el proyecto, reproduce y registra:

```powershell
python --version
python -m pip check
alembic current
node --check frontend/app.js
pytest -q -m "not oracle_integration"
pytest -q -m "not oracle_integration"
```

Resultado obligatorio de cada ejecución normal:

```text
60 passed
```

Las pruebas Oracle deben permanecer separadas y marcadas con `oracle_integration`. Si Docker, Oracle y las credenciales temporales están disponibles, ejecuta también dos veces:

```powershell
pytest -q -m oracle_integration
pytest -q -m oracle_integration
```

Resultado esperado según la línea base aprobada:

```text
11 passed
```

No elimines, relajes, cambies a `skip`, marques como `xfail` ni modifiques pruebas únicamente para obtener resultados verdes.

Si la línea base normal no produce las 60 pruebas aprobadas, detente, documenta la diferencia y corrige exclusivamente la causa demostrada antes de continuar.

---

## 2. Restricciones obligatorias

- Conserva Python, FastAPI, SQLAlchemy, SQLite interna, Oracle `oracledb`, HTML, CSS, JavaScript, Bootstrap, Alembic y Pytest.
- Oracle continúa siendo el único motor objetivo del MVP.
- SQLite continúa siendo la base interna del framework.
- No migres el frontend a React, Angular, Vue ni otro framework.
- No migres la base interna a PostgreSQL, MySQL, Supabase, Firebase ni otro servicio.
- No implementes usuarios, roles o permisos empresariales. La protección de esta fase será un acceso único y sencillo para impedir exposición pública no autorizada.
- No agregues IA, reportes PDF, CSV, gráficas complejas ni soporte multi-motor.
- No cambies el contrato funcional aprobado de proyectos, perfiles, casos, suites, ejecución e historial.
- No guardes contraseñas Oracle, claves de acceso, tokens, llaves SSH ni secretos en Git, SQLite, código, documentación, capturas, logs o ZIP.
- No publiques Oracle en el puerto `1521` hacia Internet.
- No utilices una base Oracle de producción.
- No ejecutes `COMMIT` para las pruebas DML.
- No sustituyas el rollback obligatorio.
- No trabajes directamente sobre `main` si el repositorio ya dispone de ramas. Usa una rama como `fase-4-2-despliegue`.

---

## 3. Corregir primero la documentación desactualizada

El `README.md` todavía presenta la validación Oracle real como pendiente, aunque la Fase 4.1.1 fue aprobada.

Corrige el README para que indique con exactitud:

- Oracle Database Free ya fue validado localmente en la Fase 4.1.1.
- Se aprobaron 60 pruebas normales y 11 pruebas Oracle separadas.
- La contraseña se solicita únicamente al probar o ejecutar y nunca se persiste.
- El despliegue público corresponde a esta Fase 4.2.
- El producto no debe utilizarse contra una base Oracle de producción.

No alteres informes anteriores para ocultar la evolución del proyecto. Si un informe histórico contiene una afirmación que era correcta para su fecha, consérvala y aclara el estado actual en el README y en el nuevo informe de Fase 4.2.

---

## 4. Contenerizar la aplicación FastAPI

### 4.1 Archivos mínimos

Crea, como mínimo:

```text
Dockerfile
.dockerignore
infra/
  production/
    compose.yml
    README.md
    .env.production.example
scripts/
  start_production.sh
```

Si necesitas otro archivo pequeño para mantener una solución clara y portable, justifícalo en el informe. No dupliques código ni generes archivos innecesarios.

### 4.2 Requisitos del `Dockerfile`

- Usa una imagen oficial de Python compatible y estable. Se recomienda `python:3.12-slim` únicamente si todas las dependencias y pruebas funcionan con ella.
- Instala las dependencias exclusivamente desde `requirements.txt`.
- Usa una carpeta de trabajo explícita.
- Copia solamente los archivos necesarios para ejecutar la aplicación y las migraciones.
- Ejecuta la aplicación con un usuario no root cuando sea técnicamente viable.
- Expone únicamente el puerto HTTP de FastAPI.
- No incluye `.env`, `.env.oracle`, SQLite generadas, entornos virtuales, cachés, logs, credenciales ni resultados temporales.
- Incluye un `HEALTHCHECK` que use la ruta raíz `/`, ya existente, o una comprobación equivalente sin exponer información sensible.
- No ejecuta Oracle dentro de la misma imagen de la aplicación.

### 4.3 Inicio de producción

`scripts/start_production.sh` debe:

1. utilizar `set -e`;
2. ejecutar `alembic upgrade head`;
3. iniciar Uvicorn escuchando en `0.0.0.0` y en el puerto configurado por entorno;
4. fallar con un mensaje claro si la migración no puede aplicarse;
5. no crear el esquema mediante `Base.metadata.create_all()`;
6. no imprimir secretos.

Valida sintaxis del script y permisos de ejecución.

### 4.4 `.dockerignore`

Debe excluir, como mínimo:

- `.git`;
- `.env` y todos los `.env.*`, excepto ejemplos ficticios necesarios;
- `venv`, `.venv*` y otros entornos;
- `__pycache__`, `.pytest_cache`, cobertura y compilados;
- `*.db`, `*.sqlite`, `*.sqlite3`;
- logs, temporales, evidencias sensibles y ZIP anteriores;
- configuración local del IDE.

---

## 5. Persistencia de la base interna

El contenedor de la aplicación no debe guardar la SQLite en una capa efímera.

Configura en `infra/production/compose.yml`:

- un volumen nombrado exclusivo para la base interna;
- una ruta estable, por ejemplo `/data/framework_interno.db`;
- `FRAMEWORK_DB_URL=sqlite:////data/framework_interno.db`;
- migraciones Alembic ejecutadas antes de iniciar Uvicorn;
- política de reinicio apropiada;
- healthcheck real.

Prueba obligatoriamente:

1. iniciar la composición;
2. crear un proyecto, un perfil sin contraseña, un caso y una suite;
3. reiniciar o recrear solamente el contenedor de la aplicación;
4. comprobar que los datos continúan existiendo;
5. comprobar `alembic current` dentro del contenedor;
6. documentar el nombre y función del volumen, sin copiar su contenido al repositorio.

Incluye en `infra/production/README.md` un procedimiento seguro de respaldo y restauración de la SQLite. No declares que fue probado si no se realizó realmente.

---

## 6. Oracle en la composición de producción académica

Reutiliza la infraestructura aprobada en `infra/oracle/` y evita duplicar scripts de inicialización.

La composición de producción debe permitir:

- aplicación FastAPI;
- Oracle Database Free oficial;
- red interna privada entre ambos servicios;
- volumen persistente de Oracle;
- volumen persistente de SQLite;
- healthchecks separados;
- espera controlada de disponibilidad antes de ejecutar pruebas Oracle.

Reglas:

- No publiques `1521:1521` hacia todas las interfaces.
- En un servidor remoto, utiliza solamente red interna de Docker; `1521` no debe quedar expuesto públicamente.
- Si se mantiene una publicación local para diagnóstico, enlázala exclusivamente a `127.0.0.1` y documéntala como opción de mantenimiento, no como configuración pública.
- Conserva `FREEPDB1`, el usuario exclusivo `FRAMEWORK_TEST`, cuota limitada y privilegios mínimos.
- `ORACLE_PWD` y `FRAMEWORK_TEST_PASSWORD` se proporcionan desde secretos del servidor o un archivo local excluido de Git.
- El perfil guardado por el framework debe usar el nombre DNS interno del servicio Oracle cuando ambos contenedores estén en la misma red.
- La contraseña del usuario de pruebas no debe guardarse en el perfil; se seguirá introduciendo temporalmente desde la interfaz.
- No copies ni publiques la imagen de Oracle en el repositorio.
- Si el registro oficial exige autenticación o aceptación de términos, documenta el paso manual y no lo suplantes con una imagen comunitaria.

---

## 7. Protección mínima para exposición pública

El sistema permite ejecutar SQL, por lo que no puede publicarse completamente abierto.

Implementa una protección básica de acceso único, sin crear un módulo de usuarios ni roles.

### 7.1 Comportamiento requerido

- La protección debe estar desactivada por defecto en desarrollo para conservar las pruebas y el uso local actuales.
- En producción se habilitará mediante una variable como `APP_ACCESS_ENABLED=true`.
- Usuario y contraseña de acceso deben obtenerse solo de variables o secretos del entorno.
- Usa comparación segura y no registres el valor de la contraseña.
- Cuando la protección esté habilitada, deben quedar protegidos `/ui/`, `/api/`, `/docs` y `/openapi.json`.
- La ruta raíz `/` puede mantenerse como healthcheck público con información mínima.
- `/api/execute/raw` debe quedar protegido por el mismo mecanismo; no debe existir un camino alternativo sin protección.
- La respuesta no autorizada debe ser `401` y no revelar detalles internos.
- No almacenes la clave de acceso en SQLite, JavaScript, HTML, cookies creadas por el proyecto, URLs ni archivos versionados.

Se recomienda HTTP Basic a nivel de aplicación o un mecanismo equivalente simple y portable. No construyas un sistema de registro, recuperación de contraseña, perfiles o roles.

### 7.2 Pruebas obligatorias de protección

Agrega pruebas para confirmar:

1. con protección desactivada, las 60 pruebas existentes conservan su comportamiento;
2. con protección activada, `/ui/`, `/api/projects/`, `/docs` y `/openapi.json` responden `401` sin credenciales;
3. las mismas rutas responden correctamente con credenciales válidas;
4. credenciales incorrectas reciben `401`;
5. `/` continúa disponible para healthcheck;
6. las credenciales no aparecen en respuestas, logs, HTML, JavaScript, SQLite ni archivos de entrega.

No modifiques las pruebas anteriores para acomodar una protección activa por defecto.

---

## 8. Variables de producción y secretos

Crea `infra/production/.env.production.example` con valores ficticios y comentarios claros. Debe contemplar únicamente variables realmente utilizadas, por ejemplo:

```text
FRAMEWORK_DB_URL=sqlite:////data/framework_interno.db
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://ejemplo.invalid
APP_ACCESS_ENABLED=true
APP_ACCESS_USERNAME=usuario_ficticio
APP_ACCESS_PASSWORD=contraseña_ficticia
ORACLE_PWD=contraseña_ficticia_admin
FRAMEWORK_TEST_PASSWORD=contraseña_ficticia_test
RUN_ORACLE_TESTS=0
ORACLE_HOST=oracle_db
ORACLE_PORT=1521
ORACLE_SERVICE=FREEPDB1
ORACLE_TEST_USER=FRAMEWORK_TEST
```

Reglas:

- El archivo real de producción debe quedar excluido por `.gitignore`, `.dockerignore` y el empaquetador limpio.
- No reutilices las contraseñas del laboratorio en el servidor.
- `RUN_ORACLE_TESTS` permanece en `0` durante el arranque normal.
- Habilítalo temporalmente solo al ejecutar la integración real.
- No imprimas el contenido completo del entorno en logs o informes.

---

## 9. Automatización con GitHub Actions

Crea:

```text
.github/
  workflows/
    tests.yml
    docs.yml
    deploy.yml
```

### 9.1 `tests.yml`

Debe ejecutarse en `push` y `pull_request` y realizar, como mínimo:

1. checkout;
2. configuración de Python compatible;
3. instalación desde `requirements.txt`;
4. `python -m pip check`;
5. `node --check frontend/app.js`;
6. preparación de una SQLite temporal;
7. `alembic upgrade head` sobre esa base temporal;
8. `pytest -q -m "not oracle_integration"`;
9. segunda ejecución de la misma suite normal;
10. construcción del `Dockerfile`.

No intentes levantar Oracle accidentalmente en cada `push`. Las pruebas Oracle reales deben quedar en una ejecución manual o en un entorno controlado con secretos y recursos suficientes.

### 9.2 `docs.yml`

Debe verificar, sin inventar contenido:

- existencia de README y documentos obligatorios;
- ausencia de secretos en ejemplos y documentos;
- coherencia de nombres de archivos y rutas utilizadas;
- posibilidad de generar o validar los diagramas si el proyecto los incorpora;
- empaquetado de documentación como artefacto si resulta compatible con la plataforma.

No agregues una herramienta pesada solo para aparentar automatización. Documenta exactamente qué valida el workflow.

### 9.3 `deploy.yml`

- Debe depender del éxito de las pruebas o exigir ejecución manual mediante `workflow_dispatch`.
- Debe utilizar GitHub Secrets; nunca valores directos.
- Debe apuntar al proveedor o servidor realmente elegido.
- Debe desplegar la misma imagen probada.
- Debe ejecutar migraciones antes de exponer la nueva versión.
- Debe comprobar el healthcheck después del despliegue.
- Debe fallar si la aplicación no queda saludable.
- No debe borrar volúmenes persistentes.
- No debe ejecutar `docker compose down -v`.

Si todavía no existe servidor elegido o credenciales, no inventes un workflow “validado”. Puedes dejar la estructura portable y documentada, pero marca el despliegue externo como **BLOQUEADO POR DECISIÓN/ACCESO EXTERNO** hasta disponer de datos reales.

---

## 10. Preparación del servidor

La arquitectura recomendada para conservar el proyecto aprobado es una máquina virtual o VPS Linux con Docker y Docker Compose, porque permite ejecutar la aplicación y Oracle con volúmenes persistentes sin cambiar de tecnologías.

Documenta en `infra/production/README.md`:

1. recursos mínimos recomendados y espacio requerido;
2. instalación de Docker y Compose;
3. inicio de sesión o aceptación de términos del registro oficial de Oracle;
4. creación segura del archivo de variables reales;
5. inicio y revisión de healthchecks;
6. creación del perfil Oracle interno desde la interfaz;
7. configuración de HTTPS y dominio en el proveedor o proxy elegido;
8. respaldo de ambos volúmenes;
9. actualización sin destruir datos;
10. rollback de una versión de la aplicación;
11. consulta segura de logs sin mostrar secretos;
12. detención controlada sin eliminar volúmenes.

No compres servicios, registres dominios, abras puertos ni modifiques DNS sin autorización expresa del usuario.

---

## 11. Pruebas locales de producción

Antes de cualquier despliegue externo, construye y valida localmente:

```powershell
docker build -t framework-pruebas-sql:fase-4-2 .
docker compose -f infra/production/compose.yml config
docker compose -f infra/production/compose.yml up -d --build
docker compose -f infra/production/compose.yml ps
```

Comprueba mediante HTTP y navegador:

- `/` devuelve estado saludable;
- `/ui/` exige acceso cuando la protección está habilitada;
- credenciales correctas permiten acceder;
- `/docs` y `/openapi.json` están protegidos;
- la API funciona desde la interfaz;
- proyectos, perfiles, casos y suites conservan su CRUD;
- ejecutar un caso produce PASS, FAIL o ERROR según corresponda;
- una DML registra `rollback_applied=true`;
- el historial conserva evidencia;
- reiniciar el contenedor no elimina la información interna;
- recrear la aplicación no elimina el volumen Oracle;
- el puerto 1521 no queda expuesto públicamente.

Ejecuta después las pruebas normales dos veces. Si Oracle está configurado, ejecuta también las pruebas Oracle dos veces y comprueba desde otra conexión que INSERT, UPDATE y DELETE no dejan cambios persistentes.

---

## 12. Validación del despliegue público

Esta sección solo se marca como aprobada cuando exista una URL real y accesible.

Comprueba:

1. URL mediante HTTPS.
2. Healthcheck público mínimo.
3. Acceso rechazado sin credenciales.
4. Acceso autorizado con credenciales válidas.
5. CRUD de proyectos, perfiles, casos y suites.
6. Conexión Oracle válida e inválida.
7. Ejecución SELECT con `ROW_COUNT`.
8. Ejecución SELECT con `EXISTS`.
9. INSERT, UPDATE y DELETE con rollback comprobado.
10. Resultado deliberadamente diferente registrado como FAIL.
11. SQL inválido registrado como ERROR.
12. `DROP TABLE` bloqueado antes de llegar a Oracle.
13. Historial con PASS, FAIL y ERROR.
14. Persistencia después de reiniciar o actualizar la aplicación.
15. Ausencia de contraseñas en SQLite, respuestas, logs, historial y repositorio.
16. Ejecución exitosa de los workflows definidos.

No uses datos ni credenciales reales de una organización. Utiliza únicamente el esquema exclusivo de laboratorio.

---

## 13. Seguridad y revisión de secretos

Antes de crear el ZIP o subir cambios:

- revisa `git status`;
- inspecciona únicamente nombres de variables y coincidencias potenciales, sin imprimir secretos en el informe;
- verifica que `.env`, `.env.oracle`, `.env.production` y llaves privadas estén ignoradas;
- verifica el contenido final del ZIP;
- confirma que no existan bases SQLite generadas;
- confirma que no existan volúmenes, dumps, logs, capturas con credenciales ni archivos de Docker Desktop;
- conserva solo `.env.example`, `.env.oracle.example` y `.env.production.example` con valores ficticios.

Actualiza `scripts/build_clean_zip.py` para incluir los nuevos archivos de producción y excluir cualquier secreto o artefacto generado.

El empaquetador debe fallar si encuentra:

- archivos `.env` reales;
- llaves privadas;
- contraseñas que no sean ejemplos claramente ficticios;
- bases internas;
- entornos virtuales;
- cachés;
- logs;
- ZIP anidados;
- rutas absolutas o con `..`.

---

## 14. Pruebas nuevas mínimas

Agrega pruebas reproducibles para:

1. acceso deshabilitado por defecto;
2. acceso habilitado y rechazo sin credenciales;
3. aceptación con credenciales correctas;
4. rechazo con credenciales incorrectas;
5. healthcheck disponible;
6. ausencia de secretos en respuestas y archivos públicos;
7. configuración de SQLite en ruta persistente;
8. sintaxis y presencia de archivos de producción;
9. `docker compose config` válido cuando Docker esté disponible;
10. Dockerfile construible;
11. `.dockerignore` y empaquetador excluyen archivos sensibles;
12. workflows presentes sin secretos escritos directamente.

Las pruebas que dependan realmente de Docker pueden ejecutarse como comprobaciones de integración separadas si el entorno de Pytest no dispone de Docker. No simules que una imagen se construyó cuando no se ejecutó `docker build`.

---

## 15. Documentación final

Actualiza o crea:

```text
README.md
docs/
  manual_usuario.md
  manual_tecnico.md
  arquitectura.md
  instalacion_y_despliegue.md
  diagramas/
infra/production/README.md
```

La documentación debe describir solamente lo implementado y probado. Incluye:

- arquitectura local y de producción;
- flujo Proyecto → Perfil → Caso → Suite → Ejecución → Historial;
- diferencia entre SQLite interna y Oracle objetivo;
- rollback DML;
- administración de secretos;
- protección básica de acceso;
- volúmenes persistentes;
- automatizaciones;
- instalación limpia;
- actualización y recuperación;
- URL pública únicamente cuando exista;
- limitaciones reales.

Los diagramas pueden escribirse en Mermaid o PlantUML y deben corresponder al código final.

---

## 16. Entregables

Genera:

```text
FASE_4_2_PREPARACION_Y_DESPLIEGUE.md
RESULTADO_FASE_4_2.md
Fase_4_2_Limpio.zip
```

El informe `RESULTADO_FASE_4_2.md` debe contener:

- fecha y entorno real;
- rama utilizada;
- archivos creados y modificados;
- decisiones técnicas justificadas;
- versiones reales;
- comandos ejecutados;
- salidas exactas de pruebas normales;
- salidas exactas de pruebas Oracle, si fueron ejecutadas;
- resultado del build Docker;
- resultado de `docker compose config`;
- resultado de persistencia después del reinicio;
- resultado de acceso autorizado y no autorizado;
- workflows creados y estado real de ejecución;
- URL pública, solo si existe;
- evidencia del rollback DML;
- confirmación de que no se persistieron secretos;
- contenido y validación del ZIP limpio;
- limitaciones y bloqueos reales;
- conclusión `APROBADO LOCALMENTE`, `APROBADO Y DESPLEGADO` o `BLOQUEADO`, según la evidencia.

Si no existe todavía servidor o dominio, el resultado correcto será **APROBADO LOCALMENTE PARA DESPLIEGUE**, indicando exactamente qué datos externos faltan. No marques como desplegado un proyecto que solo fue probado en Docker local.

---

## 17. Criterio de cierre

La Fase 4.2 queda **APROBADA LOCALMENTE PARA DESPLIEGUE** únicamente si:

- [ ] las 60 pruebas normales pasan dos veces;
- [ ] las pruebas nuevas de producción pasan;
- [ ] las pruebas Oracle siguen separadas;
- [ ] el Dockerfile se construye;
- [ ] `docker compose config` es válido;
- [ ] la aplicación y Oracle alcanzan estado saludable localmente;
- [ ] la SQLite y Oracle conservan datos después de recrear contenedores;
- [ ] el acceso está protegido al habilitar producción;
- [ ] los secretos no se persisten ni empaquetan;
- [ ] los workflows existen y son coherentes;
- [ ] la documentación permite reproducir el entorno;
- [ ] el ZIP limpio supera la validación.

La Fase 4.2 queda **APROBADA Y DESPLEGADA** solamente si, además:

- [ ] existe una URL pública HTTPS real;
- [ ] el acceso no autorizado es rechazado;
- [ ] los volúmenes persistentes están configurados en el servidor;
- [ ] Oracle no expone públicamente el puerto 1521;
- [ ] se validó el flujo principal en la URL publicada;
- [ ] se demostraron PASS, FAIL, ERROR y rollback;
- [ ] el workflow de despliegue se ejecutó realmente;
- [ ] la aplicación continúa operativa después de una actualización o reinicio.

---

## 18. Respuesta final esperada de Antigravity

Al terminar, responde de forma breve con:

1. estado final real;
2. total de pruebas normales, nuevas y Oracle;
3. archivos principales creados;
4. resultado de Docker y persistencia;
5. estado de protección de acceso;
6. estado de GitHub Actions;
7. URL pública, si existe;
8. bloqueos externos pendientes;
9. nombre y ubicación del ZIP y del informe.

No respondas “todo listo” sin mostrar resultados verificables. No escribas ni muestres contraseñas.

