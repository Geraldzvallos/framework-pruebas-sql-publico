# RESULTADO PREPARACIÓN Y DESPLIEGUE (Fase 4.2)

## 1. Entorno y Versiones
- **Python**: 3.12 (slim en Docker) / 3.14.0 (local)
- **Node**: 22.11.0 (local)
- **Docker**: Activo, Compose v2
- **Motor Interno**: SQLite (`framework_interno.db`)
- **Motor Objetivo**: Oracle Database Free
- **Dependencias**: Aprobadas (`pip check` sin errores)

## 2. Archivos Principales
- `infra/production/compose.yml` (Nombres y rutas correctas: `name: framework_pruebas_sql`, imagen compilada)
- `infra/production/.env.production.example` (Versionado correctamente en `.gitignore`)
- `scripts/start_production.sh` (Usando `$API_HOST` y `$API_PORT`)
- `.github/workflows/deploy.yml` (Bloqueo explícito `exit 1` por falta de secretos y servidor)
- `.github/workflows/docs.yml` (Revisión de manuales técnicos, arquitectura y de usuario)
- `tests/test_production_config.py` (Tests de variables, Compose, secret exclusion)
- `docs/manual_usuario.md`, `docs/manual_tecnico.md`, `docs/arquitectura.md`, `docs/instalacion_y_despliegue.md`

## 3. Resultado de Docker y Persistencia
Comandos ejecutados:
```bash
docker build -t framework-pruebas-sql:fase-4-2 .
docker compose -f infra/production/compose.yml --env-file infra/production/.env.production up -d --build
docker ps -a
```
Resultados:
- La imagen `framework-pruebas-sql:fase-4-2` fue compilada exitosamente.
- `framework_api_prod` arrancó correctamente y su estado es `Up 18 minutes (healthy)`.
- **Fallo:** `framework_oracle_prod` se quedó atascado en estado `Created` (no arrancó), probablemente por límites de memoria o bloqueos de Docker Desktop con un contenedor anterior (`framework_oracle_db`).
- Los volúmenes `framework_pruebas_sql_framework_data` y `framework_pruebas_sql_oracle_data` fueron creados correctamente.
- No se pudo comprobar la conservación de datos tras recrear la API de forma integrada con Oracle debido al fallo de Oracle.

## 4. Estado de Protección de Acceso
- El acceso web (`/ui`) y de la API (`/api`) requiere de autenticación HTTP Basic.
- Las solicitudes sin credenciales retornan código `401 Unauthorized`.
- Las credenciales reales se mantienen estrictamente dentro de `.env.production` (ignorado en Git).

## 5. Estado de Pruebas
Se ejecutaron repetidamente las pruebas usando `pytest -q -m "not oracle_integration"`.
Resultados de dos ejecuciones consecutivas (73 pruebas):
```
........................................................................ [ 98%]
.                                                                        [100%]
73 passed, 11 deselected in 11.94s

........................................................................ [ 98%]
.                                                                        [100%]
73 passed, 11 deselected in 11.84s
```
*Nota: Las 11 pruebas Oracle de integración no se pudieron ejecutar debido a que el contenedor Oracle no logró arrancar exitosamente.*

Criterios del empaquetador ZIP verificados mediante pruebas dinámicas (`tests/test_production_config.py`):
```
........                                                                 [100%]
8 passed in 0.19s
```
El script `build_clean_zip.py` falla adecuadamente frente a secretos reales y `.env`. No imprime los valores de las contraseñas reales.

## 6. Bloqueos Externos Pendientes
- **Infraestructura Cloud**: Servidor/VPS Linux con IP pública y > 3 GB de RAM no disponible aún.
- **Dominio y Certificados TLS**: Configuración HTTPS y proxy reverso (Nginx/Traefik) no implementada.
- **Acceso Remoto SSH**: No se han proporcionado las llaves para el pipeline de GitHub Actions.
- **GitHub Secrets**: Las variables de entorno de producción no están creadas en GitHub.
- **Workflows**: Los workflows `docs.yml` y `deploy.yml` existen y fueron corregidos, pero todavía no fueron ejecutados en GitHub porque los cambios aún no han sido publicados.

## 7. Entregables
- Archivo ZIP final: `Fase_4_2_Limpio.zip` generado mediante `scripts/build_clean_zip.py`.

**ESTADO ACTUAL**: BLOQUEADO PARA CIERRE LOCAL (La persistencia de Oracle y el despliegue integrado no pudieron ser validados localmente debido a que el contenedor de Oracle no logró arrancar por recursos o bloqueos de Docker).
