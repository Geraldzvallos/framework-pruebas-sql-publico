# Instalación y Despliegue

## Requisitos Previos
- Docker y Docker Compose instalados en el entorno destino.
- Acceso a `container-registry.oracle.com` (requiere login).

## Procedimiento de Despliegue Limpio

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
Si surge un error, etiquete y despliegue la imagen anterior:
```bash
docker tag framework_pruebas_sql:version_anterior framework-pruebas-sql:fase-4-2
docker compose -f infra/production/compose.yml --env-file infra/production/.env.production up -d --no-deps api
```
