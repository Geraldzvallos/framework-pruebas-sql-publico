# FASE 4.2.2 — SEGURIDAD Y CIERRE PREDESPLIEGUE

## Framework de pruebas de base de datos SQL

### Propósito

Esta fase corrige únicamente los pendientes reales encontrados durante la auditoría del proyecto antes del despliegue público. No agrega módulos funcionales nuevos ni modifica el alcance académico aprobado.

La línea base comprobada es:

- 73 pruebas normales aprobadas dos veces.
- 11 pruebas Oracle existentes y separadas mediante `oracle_integration`.
- 15 pruebas específicas de autenticación, producción y frontend aprobadas.
- Dependencias sin conflictos mediante `pip check`.
- Sintaxis de `frontend/app.js` válida.
- Empaquetador capaz de generar un ZIP limpio de 101 entradas, aunque todavía debe reforzarse para nombres escritos en mayúsculas.

El proyecto todavía no debe desplegarse públicamente. Primero debe completar esta fase y quedar aprobado mediante evidencias reproducibles.

---

## 1. Instrucción principal para Antigravity IDE

Trabaja exclusivamente sobre el repositorio oficial actualmente abierto:

```text
C:\Users\MSI\Downloads\proyecto-group-4-trabajo
```

El código del framework se encuentra en:

```text
framework-pruebas-sql/
```

Debes permanecer en la rama:

```text
fase-4-2-despliegue
```

No trabajes directamente sobre `main`, no crees otro proyecto, no dupliques el repositorio y no realices todavía un despliegue público.

Antes de modificar cualquier archivo, lee completamente:

1. `README.md` de la raíz académica.
2. `framework-pruebas-sql/AGENTS.md`.
3. `framework-pruebas-sql/README.md`.
4. `framework-pruebas-sql/FASE_4_2_PREPARACION_Y_DESPLIEGUE.md`.
5. `framework-pruebas-sql/RESULTADO_FASE_4_2.md`.
6. `framework-pruebas-sql/.gitignore`.
7. `framework-pruebas-sql/.dockerignore`.
8. `framework-pruebas-sql/app/main.py`.
9. `framework-pruebas-sql/infra/production/compose.yml`.
10. `framework-pruebas-sql/scripts/build_clean_zip.py`.
11. Los workflows existentes tanto en la raíz oficial como dentro del framework.

Primero presenta un plan breve y después continúa con la implementación. Solo debes detenerte si una acción requiere borrar datos, eliminar volúmenes, cambiar `main`, utilizar credenciales no disponibles o acceder a infraestructura externa todavía no proporcionada.

---

## 2. Restricciones obligatorias

- Conserva Python, FastAPI, SQLAlchemy, SQLite, Oracle, `oracledb`, HTML, CSS, JavaScript, Bootstrap, Alembic y Pytest.
- No agregues usuarios, roles empresariales, IA, reportes PDF, CSV, gráficas complejas ni soporte para otros motores.
- No cambies el flujo de proyectos, perfiles, casos, suites, ejecución e historial.
- No elimines ni relajes pruebas para obtener resultados verdes.
- No marques pruebas nuevas como `skip` o `xfail` para ocultar fallos.
- No muestres, copies ni imprimas valores de contraseñas.
- No incluyas contraseñas en comandos visibles, documentación, logs, commits o mensajes finales.
- No abras ni reproduzcas el contenido de `.env`, `.env.oracle` o `.env.production` en la respuesta.
- No agregues al repositorio archivos `.env` reales, bases SQLite, ZIP, logs, cachés, llaves o entornos virtuales.
- No borres archivos `.env` locales: deben conservarse para las pruebas, pero seguir ignorados por Git.
- No borres contenedores ni volúmenes existentes sin autorización explícita.
- No ejecutes `docker compose down -v`.
- No expongas Oracle en `0.0.0.0:1521`.
- No despliegues, no crees DNS, no configures un servidor externo y no hagas merge a `main` en esta fase.
- Conserva intactos `.classroom50.yaml`, los archivos FD01–FD06, `media/` y los workflows de GitHub Classroom.
- Nunca afirmes que una prueba pasó si no fue ejecutada y observada.

---

## 3. Preverificación obligatoria

Desde la raíz oficial ejecuta y registra, sin revelar secretos:

```powershell
git branch --show-current
git status --short
git log -1 --oneline
git remote -v
```

Resultado obligatorio:

- rama `fase-4-2-despliegue`;
- ningún cambio previo ajeno a esta fase;
- remoto correspondiente al repositorio oficial del grupo.

Si existen cambios previos, no los descartes. Identifica su origen y detente si se superponen con esta fase.

Comprueba los archivos sensibles versionados con comandos que muestren únicamente rutas, nunca contenidos:

```powershell
git ls-files | Where-Object {
    $_ -match '(^|/)\.env($|\.)' -and $_ -notmatch '\.example$'
}

git ls-files | Where-Object {
    $_ -match '(^|/)(__pycache__|\.pytest_cache)(/|$)|\.(db|sqlite|sqlite3|pyc|pyo|pyd|zip|log|pem|key)$'
}
```

Ambos comandos deben quedar sin resultados. Si muestran archivos prohibidos:

1. no enseñes su contenido;
2. comprueba que existan reglas correctas en `.gitignore`;
3. retíralos únicamente del índice mediante `git rm --cached`, conservando el archivo local cuando sea necesario;
4. documenta solo las rutas retiradas;
5. no reescribas el historial Git en esta fase.

---

## 4. Corrección 1 — Autenticación con fallo seguro

### Problema reproducido

Cuando `APP_ACCESS_ENABLED=true` y `APP_ACCESS_USERNAME` o `APP_ACCESS_PASSWORD` están vacíos, una cabecera HTTP Basic vacía puede ser aceptada. Esto impide considerar segura la publicación.

### Resultado requerido

Corrige `framework-pruebas-sql/app/main.py` para que:

1. Si la protección está deshabilitada explícitamente, conserve el comportamiento local actual.
2. Si la protección está habilitada y falta el usuario o la contraseña, la aplicación falle de forma segura.
3. Ninguna combinación vacía o compuesta solo por espacios obtenga acceso.
4. El healthcheck indique configuración inválida y el contenedor no sea considerado saludable cuando falten las credenciales obligatorias.
5. Las credenciales válidas continúen comparándose mediante `secrets.compare_digest`.
6. Las respuestas nunca devuelvan el usuario esperado ni la contraseña esperada.

No implementes un sistema de usuarios. Se mantiene el acceso único mediante HTTP Basic previsto para el MVP académico.

### Pruebas obligatorias

Amplía `tests/test_auth.py` para verificar como mínimo:

- protección deshabilitada;
- acceso sin cabecera cuando la protección está habilitada: `401`;
- credenciales válidas: acceso permitido;
- credenciales incorrectas: `401`;
- usuario vacío con protección habilitada: servicio no disponible o fallo seguro;
- contraseña vacía con protección habilitada: servicio no disponible o fallo seguro;
- valores compuestos solo por espacios: fallo seguro;
- ningún mensaje contiene las credenciales recibidas o esperadas.

Elige un código coherente para configuración inválida, preferentemente `503 Service Unavailable`, y úsalo de forma consistente.

---

## 5. Corrección 2 — Variables obligatorias y exposición de puertos

Modifica `framework-pruebas-sql/infra/production/compose.yml` sin incluir valores reales.

### Variables obligatorias

La composición debe fallar antes de iniciar si faltan:

- `CORS_ORIGINS`;
- `APP_ACCESS_USERNAME`;
- `APP_ACCESS_PASSWORD`;
- `ORACLE_PWD`;
- `FRAMEWORK_TEST_PASSWORD`.

Utiliza la sintaxis obligatoria de Docker Compose, por ejemplo `${VARIABLE:?mensaje}`, siempre que sea compatible con la versión utilizada.

En la configuración académica de producción, `APP_ACCESS_ENABLED` debe permanecer activado. No permitas un despliegue público accidentalmente desprotegido.

### Puerto de la API

Hasta que exista el proxy HTTPS, la API debe quedar ligada únicamente al host local del servidor:

```yaml
ports:
  - "127.0.0.1:${API_PORT:-8000}:8000"
```

Oracle debe continuar ligado exclusivamente a `127.0.0.1` para diagnóstico local o permanecer solo en la red interna de Docker. Nunca publiques `1521` hacia Internet.

### Imagen Oracle reproducible

No inventes un tag. Obtén la referencia exacta de la imagen ya validada localmente mediante Docker. Si existe un digest, prefiérelo. Sustituye `:latest` únicamente por una referencia realmente instalada y comprobada.

Si no puedes determinar una versión o digest válido, conserva el hallazgo como bloqueo y no inventes una referencia.

### Validación

Ejecuta, sin imprimir valores:

```powershell
docker compose -f framework-pruebas-sql/infra/production/compose.yml --env-file framework-pruebas-sql/infra/production/.env.production config --quiet
```

También prueba que la composición falle claramente al omitir cada variable obligatoria. Realiza esta prueba con valores ficticios o en un entorno temporal; no muestres secretos reales.

---

## 6. Corrección 3 — Empaquetado limpio y seguro

Corrige `framework-pruebas-sql/scripts/build_clean_zip.py`.

### Requisitos

1. Todas las comparaciones de nombres y extensiones sensibles deben ser independientes de mayúsculas y minúsculas.
2. Debe bloquear, entre otras variantes:
   - `.env`, `.ENV`, `.Env`;
   - `.env.production`, `.ENV.PRODUCTION`;
   - `.db`, `.DB`;
   - `.sqlite`, `.SQLITE`;
   - `.zip`, `.ZIP`;
   - `.log`, `.LOG`;
   - `.pem`, `.PEM`;
   - `.key`, `.KEY`;
   - `__pycache__` y variantes de capitalización;
   - `.pytest_cache` y variantes de capitalización;
   - `venv`, `.venv*`, `*-venv` y `*_venv`.
3. Debe seguir permitiendo únicamente las plantillas ficticias terminadas exactamente en `.example`.
4. Nunca debe imprimir el valor de un secreto detectado.
5. Debe rechazar rutas absolutas, retrocesos `..` y separadores inválidos.
6. Debe excluir la SQLite generada y todos los ZIP anteriores.
7. Debe generar el artefacto dentro de un directorio controlado `dist/` o mediante un parámetro `--output` explícito.
8. `dist/` debe quedar ignorado por Git y Docker.
9. La ejecución desde `framework-pruebas-sql/` no debe dejar un ZIP rastreable en la raíz académica.

### Pruebas obligatorias

Amplía `tests/test_production_config.py` para comprobar:

- variantes mayúsculas y mixtas de archivos prohibidos;
- `.env` dentro de subdirectorios;
- bases y ZIP en mayúsculas;
- exclusión de `dist/`;
- aceptación de ejemplos ficticios;
- rechazo de contraseñas no ficticias;
- ausencia del valor secreto en `stdout` y `stderr`;
- ZIP final sin rutas absolutas ni `..`.

Después genera un ZIP real y valida su inventario. No uses ni compartas el ZIP manual que contiene los archivos locales sensibles.

---

## 7. Corrección 4 — Reglas de exclusión en el repositorio oficial

La aplicación se encuentra dentro de `framework-pruebas-sql/`, pero el empaquetado puede generar artefactos cerca de la raíz académica.

Revisa el `.gitignore` de la raíz oficial. Si no existe, crea uno mínimo; si existe, conserva todas sus reglas y añade únicamente lo necesario.

Debe impedir el seguimiento de:

```gitignore
*.zip
*.db
*.sqlite
*.sqlite3
*.log
*.pem
*.key
.env
.env.*
!.env.example
!.env.oracle.example
!.env.production.example
__pycache__/
.pytest_cache/
venv/
.venv/
.venv*/
dist/
```

No ignores ni elimines los documentos académicos, archivos `.docx`, Markdown, `media/`, `.classroom50.yaml` o workflows de Classroom.

Al terminar, repite las consultas de `git ls-files` de la preverificación y confirma que no aparece ningún archivo prohibido.

---

## 8. Corrección 5 — Backup, restauración y rollback realistas

Actualiza:

- `framework-pruebas-sql/infra/production/README.md`;
- `framework-pruebas-sql/docs/instalacion_y_despliegue.md`;
- `framework-pruebas-sql/docs/manual_tecnico.md`, únicamente si corresponde.

### Debe quedar documentado

1. Respaldo consistente de la SQLite con la API detenida o mediante un método seguro.
2. Restauración de la SQLite en el volumen nombrado.
3. Respaldo offline del volumen Oracle con el contenedor detenido de forma controlada.
4. Restauración del volumen Oracle sin publicar el puerto y sin usar `down -v` sobre los datos originales.
5. Validación posterior mediante healthchecks y consultas de verificación.
6. Ubicación y permisos seguros de los archivos de respaldo.
7. Advertencia de que los respaldos pueden contener información sensible y nunca deben subirse a Git.

### Corrección documental obligatoria

No afirmes que `alembic downgrade` es un mecanismo disponible si la migración correspondiente no implementa realmente el downgrade.

Elige una de estas opciones:

- implementar y probar un downgrade seguro; o
- documentar que, ante cambios de esquema, el rollback se realiza restaurando el respaldo previo y desplegando la imagen anterior.

Para esta fase se recomienda la segunda opción, porque es más segura y no exige alterar migraciones históricas.

### Validación mínima

Prueba realmente el respaldo y restauración de SQLite utilizando datos temporales o un volumen temporal. No utilices ni destruyas los datos originales.

La restauración completa de Oracle puede quedar como prueba obligatoria de la Fase 4.3 si no existe capacidad local suficiente. Si no se ejecuta, indícala como pendiente; no declares que fue probada.

---

## 9. Corrección 6 — Exactitud de la interfaz

Realiza únicamente ajustes pequeños, sin crear módulos nuevos:

1. Revisa las solicitudes de proyectos, conexiones, casos y suites. Actualmente la API usa un límite predeterminado de 10; la interfaz no debe ocultar registros sin informarlo.
2. Para el MVP, utiliza de forma explícita `limit=100` o incorpora paginación sencilla reutilizando la existente.
3. Los indicadores del dashboard consultan como máximo 100 ejecuciones. No deben presentarse engañosamente como totales absolutos.
4. Aplica una solución mínima y clara:
   - mostrar “Últimas 100 ejecuciones”, o
   - calcular totales completos mediante una solución paginada o endpoint de resumen con pruebas.
5. Conserva el escape de HTML y no introduzcas `innerHTML` con datos del usuario sin saneamiento.

No agregues gráficas ni reportes.

---

## 10. GitHub Actions en el repositorio oficial

GitHub solo ejecuta workflows situados en `.github/workflows/` en la raíz oficial. Los workflows ubicados dentro de `framework-pruebas-sql/.github/workflows/` no son suficientes cuando el framework es una subcarpeta.

Verifica en la raíz oficial:

```text
.github/workflows/tests.yml
.github/workflows/docs.yml
.github/workflows/deploy.yml
```

### Reglas

- No borres ni reemplaces workflows de GitHub Classroom.
- Configura `working-directory: ./framework-pruebas-sql` para pasos `run` relacionados con la aplicación.
- `actions/checkout` y `actions/setup-python` no requieren ese directorio.
- `tests.yml` debe instalar dependencias, ejecutar `pip check`, validar JavaScript, aplicar migraciones en una SQLite temporal, ejecutar dos veces las pruebas no Oracle y construir la imagen Docker.
- `docs.yml` debe comprobar los documentos y ejecutar el empaquetador limpio.
- `deploy.yml` debe continuar siendo manual y no debe desplegar mientras falten servidor, dominio y secretos.
- No agregues secretos ficticios a GitHub Actions.
- No declares que Actions pasó hasta observar la ejecución real en GitHub.

Si los workflows ya cumplen estos requisitos, no los reescribas innecesariamente.

---

## 11. Ejecución completa de pruebas

### 11.1 Pruebas normales

Desde `framework-pruebas-sql/`, activa el entorno correcto y ejecuta:

```powershell
python --version
python -m pip check
node --check frontend/app.js
alembic current
pytest -q -m "not oracle_integration"
pytest -q -m "not oracle_integration"
```

La línea base anterior era de 73 pruebas normales. Como esta fase añade pruebas, el total final debe ser mayor o igual a 73. No reduzcas el número de pruebas y no aumentes exclusiones.

### 11.2 Pruebas específicas nuevas

Ejecuta directamente:

```powershell
pytest -q tests/test_auth.py tests/test_production_config.py tests/test_revision_final_frontend.py
```

Todas deben aprobar.

### 11.3 Oracle real

Si el contenedor Oracle local se encuentra disponible y saludable, carga las variables desde el archivo local ignorado sin imprimirlas y ejecuta:

```powershell
pytest -q -m oracle_integration
pytest -q -m oracle_integration
```

Resultado esperado según la línea base: 11 pruebas aprobadas en cada ejecución.

Si Oracle no está disponible, documenta el bloqueo real. No conviertas las pruebas omitidas en pruebas aprobadas.

### 11.4 Docker y persistencia

Sin eliminar volúmenes:

1. valida la configuración de Compose;
2. construye la imagen de la API;
3. inicia los servicios;
4. confirma que API y Oracle estén `healthy`;
5. verifica `401` sin credenciales;
6. verifica acceso con credenciales válidas;
7. verifica fallo seguro cuando faltan credenciales obligatorias usando un entorno temporal;
8. recrea únicamente la API;
9. confirma que proyectos, perfiles, casos, suites e historial siguen presentes;
10. no declares persistencia comprobada solamente por observar que existe un volumen.

---

## 12. Comprobación final de secretos y archivos prohibidos

Antes del commit ejecuta desde la raíz oficial:

```powershell
git status --short
git diff --check
git diff --cached --name-only

git ls-files | Where-Object {
    $_ -match '(^|/)\.env($|\.)' -and $_ -notmatch '\.example$'
}

git ls-files | Where-Object {
    $_ -match '(^|/)(__pycache__|\.pytest_cache)(/|$)|\.(db|sqlite|sqlite3|pyc|pyo|pyd|zip|log|pem|key)$'
}
```

Los dos últimos comandos deben quedar sin resultados.

No utilices comandos que impriman el contenido de los archivos `.env`. No incluyas valores secretos en el informe final.

Las credenciales utilizadas en el ZIP manual auditado deben considerarse expuestas y no deben reutilizarse en el despliegue público. Registra únicamente esta obligación, nunca sus valores.

---

## 13. Informe de la fase

Crea:

```text
framework-pruebas-sql/RESULTADO_FASE_4_2_2.md
```

Debe contener únicamente resultados verificables:

1. fecha y entorno;
2. rama y commit base;
3. archivos modificados;
4. explicación breve de cada corrección;
5. comandos ejecutados;
6. total exacto de pruebas normales en ambas ejecuciones;
7. total exacto de pruebas Oracle en ambas ejecuciones, o bloqueo real;
8. resultado de Docker y healthchecks;
9. resultado de persistencia tras recrear solo la API;
10. resultado de la prueba temporal de backup y restauración SQLite;
11. inventario del ZIP limpio;
12. comprobación de archivos prohibidos;
13. estado de GitHub Actions, únicamente si ya fue observado remotamente;
14. pendientes externos para la Fase 4.3.

Usa uno de estos estados:

```text
APROBADO PARA INTEGRACIÓN
```

solo cuando todas las verificaciones locales obligatorias hayan pasado; o:

```text
BLOQUEADO PARA INTEGRACIÓN
```

cuando exista algún fallo pendiente.

No uses todavía “DESPLEGADO”, “PRODUCCIÓN APROBADA” ni inventes una URL pública.

---

## 14. Commit y subida controlada

Antes de crear el commit, muestra únicamente las rutas modificadas y confirma que no existen archivos prohibidos.

Si todo está aprobado:

```powershell
git add .github .gitignore framework-pruebas-sql
git status
git diff --cached --check
git commit -m "fix: endurecer seguridad y cierre predespliegue"
git push origin fase-4-2-despliegue
```

No uses `git add -f`. No hagas merge a `main`.

Si Git solicita autenticación o aprobación gráfica, detente y pide al usuario completar únicamente ese paso. No intentes extraer ni reutilizar credenciales.

Después del `push`, indica que el usuario debe revisar GitHub Actions. No afirmes que están verdes sin observarlas.

---

## 15. Criterios de aprobación de la Fase 4.2.2

La fase se considera aprobada únicamente cuando:

- no hay secretos ni archivos prohibidos rastreados por Git;
- el ZIP limpio no incluye secretos, bases, cachés ni ZIP anidados;
- el empaquetador bloquea variantes de mayúsculas y minúsculas;
- la aplicación rechaza una configuración de autenticación incompleta;
- las credenciales válidas continúan funcionando;
- Compose exige secretos y no expone directamente la API ni Oracle hacia Internet;
- la imagen Oracle queda fijada a una referencia realmente comprobada, o el punto queda documentado como bloqueo;
- el procedimiento de restauración no promete un `alembic downgrade` inexistente;
- el respaldo y restauración temporal de SQLite se prueban realmente;
- las pruebas normales pasan dos veces sin reducir su cantidad;
- las pruebas Oracle pasan dos veces si el entorno local está disponible;
- Docker conserva los datos al recrear únicamente la API;
- la documentación coincide con el comportamiento real;
- el commit no contiene `.env`, bases, ZIP, llaves, logs ni cachés;
- el resultado final no inventa pruebas, URLs ni despliegues.

---

## 16. Respuesta final esperada de Antigravity

Al terminar, responde de forma breve y verificable con:

1. estado final de la fase;
2. lista de archivos modificados;
3. total exacto de pruebas normales, primera y segunda ejecución;
4. total exacto de pruebas Oracle, primera y segunda ejecución, o motivo del bloqueo;
5. resultado de Docker y healthchecks;
6. resultado de autenticación vacía, inválida y válida;
7. resultado de persistencia;
8. resultado del respaldo/restauración SQLite;
9. ruta y número de entradas del ZIP limpio;
10. confirmación de que no existen archivos prohibidos rastreados;
11. commit creado y estado del `push`;
12. estado real de GitHub Actions si pudo observarse;
13. pendientes externos exactos para comenzar la Fase 4.3.

No respondas “todo listo” sin adjuntar estos resultados. No muestres contraseñas.
