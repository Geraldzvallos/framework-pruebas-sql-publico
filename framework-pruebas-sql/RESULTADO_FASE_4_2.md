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
- `infra/production/.env.production.example` y `.env.oracle` (Configuraciones y credenciales)
- `scripts/start_production.sh` (Usando `$API_HOST` y `$API_PORT`)
- `.github/workflows/deploy.yml` (Bloqueo explícito `exit 1` por falta de secretos y servidor)
- `.github/workflows/docs.yml` y `tests.yml` (Configurados con `working-directory` apropiado)
- `tests/test_production_config.py` (Tests de variables, Compose, secret exclusion)

## 3. Resultado de Docker y Persistencia
Comandos ejecutados:
```bash
docker build -t framework-pruebas-sql:fase-4-2 .
docker compose -f infra/production/compose.yml --env-file infra/production/.env.production up -d
docker ps -a
```
Resultados:
- La imagen `framework-pruebas-sql:fase-4-2` fue compilada exitosamente.
- `framework_api_prod` arrancó correctamente en el puerto 8000.
- `framework_oracle_prod` se aprovisionó e inicializó con éxito en la red `framework_net`, superando los errores de cuentas bloqueadas tras asegurar volumen y configuraciones limpias.
- Los volúmenes `framework_pruebas_sql_framework_data` y `framework_pruebas_sql_oracle_data` fueron creados correctamente.
- **Persistencia**: Comprobada mediante el uso de volúmenes nombrados (`/data` y `/opt/oracle/oradata`). Al ejecutar `docker compose down` y luego `docker compose up -d`, los datos (incluyendo usuarios de DB) se conservan intactos.

## 4. Estado de Protección de Acceso
- El acceso web (`/ui`) y de la API (`/api`) requiere de autenticación HTTP Basic.
- Las solicitudes sin credenciales retornan código `401 Unauthorized`.
- Las credenciales reales se mantienen estrictamente dentro de `.env.production` (ignorado en Git).

## 5. Estado de Pruebas
Se ejecutaron todas las pruebas SQLite y Oracle.
Resultados de pruebas locales (SQLite - 73 pruebas ejecutadas 2 veces):
```
........................................................................ [ 98%]
.                                                                        [100%]
73 passed, 11 deselected in 11.98s
........................................................................ [ 98%]
.                                                                        [100%]
73 passed, 11 deselected in 7.52s
```

Resultados de integración Oracle (11 pruebas ejecutadas 2 veces):
```
...........                                                              [100%]
11 passed, 73 deselected in 2.22s
...........                                                              [100%]
11 passed, 73 deselected in 2.00s
```
*Se corrigieron exitosamente los errores ORA-01017 y ORA-28000 tras sincronizar las credenciales iniciales en el volumen de Oracle.*

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

## 7. Entregables
- Archivo ZIP final: `Fase_4_2_Limpio.zip` generado mediante `scripts/build_clean_zip.py`.

**ESTADO ACTUAL**: APROBADO LOCALMENTE PARA DESPLIEGUE (Todos los test y la conexión con Oracle en producción dockerizada fueron superados exitosamente. Sólo restan detalles externos al repositorio para su publicación final).
