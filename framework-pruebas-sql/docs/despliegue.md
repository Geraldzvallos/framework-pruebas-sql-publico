# Despliegue (Docker)

## Requisitos Previos
- Docker y Docker Compose instalados en el entorno destino.
- Acceso a `container-registry.oracle.com` (requiere login si usa imágenes oficiales protegidas).

## Procedimiento de Despliegue Limpio (Local/Staging)

1. Clone el repositorio y sitúese en la raíz.
2. Copie el archivo de ejemplo a su archivo de configuración de producción:
   ```bash
   cp infra/production/.env.production.example infra/production/.env.production
   ```
3. Edite `infra/production/.env.production` agregando contraseñas seguras y habilitando la protección (`APP_ACCESS_ENABLED=true`). NUNCA suba este archivo a repositorios públicos.
4. Lance el conjunto de contenedores:
   ```bash
   docker compose -f infra/production/compose.yml --env-file infra/production/.env.production up -d --build
   ```
5. Verifique el estado:
   ```bash
   docker compose -f infra/production/compose.yml --env-file infra/production/.env.production ps
   ```

## Actualización y Rollback
**Actualización:**
Descargue los nuevos cambios mediante `git pull` y recompile solo la API, sin destruir los datos de volumen:
```bash
docker compose -f infra/production/compose.yml --env-file infra/production/.env.production build api
docker compose -f infra/production/compose.yml --env-file infra/production/.env.production up -d --no-deps api
```

**Rollback:**
Si surge un error, o existen problemas de datos tras la actualización:
1. Detenga los contenedores temporalmente: `docker compose down`.
2. Restaure los backups de sus volúmenes (SQLite y Oracle) obtenidos antes de la actualización.
3. Etiquete y despliegue la imagen anterior:
```bash
docker tag sql-qa-framework:version_anterior sql-qa-framework:latest
docker compose -f infra/production/compose.yml --env-file infra/production/.env.production up -d
```
*Nota: No utilice `alembic downgrade`. El rollback de base de datos se realiza restaurando los volúmenes físicos respaldados.*

> [!NOTE]
> El despliegue cloud definitivo continúa pendiente de configuración DNS y variables de entorno finales.
