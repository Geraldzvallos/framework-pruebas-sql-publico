# Despliegue de Producción (Académica)

Esta carpeta contiene la configuración necesaria para ejecutar el Framework de Pruebas SQL en un entorno de producción o pruebas integrado utilizando Docker y Docker Compose.

## 1. Recursos mínimos recomendados
- 1 vCPU
- 3 GB de RAM (Oracle Free requiere al menos 2 GB de memoria).
- 10 GB de espacio en disco (principalmente para la imagen de Oracle y sus volúmenes persistentes).

## 2. Instalación de Docker y Compose
Para desplegar este entorno, es necesario tener instalados Docker y Docker Compose en el servidor VPS o máquina virtual Linux.
Para instalar Docker en Debian/Ubuntu:
```bash
sudo apt update
sudo apt install docker.io docker-compose-v2
```

## 3. Registro Oficial de Oracle
Para descargar la imagen oficial de Oracle Database Free, es necesario contar con una cuenta en Oracle Container Registry.
1. Visita https://container-registry.oracle.com/ y acepta los términos de licencia para la base de datos "Database Free".
2. En el servidor, inicia sesión con:
   ```bash
   docker login container-registry.oracle.com
   ```

## 4. Creación segura del archivo de variables
Copia el archivo de ejemplo para crear tu configuración real. **Nunca subas este archivo al repositorio**.
```bash
cp .env.production.example .env.production
```
Edita `.env.production` y asegúrate de cambiar todas las contraseñas ficticias por contraseñas reales, fuertes y seguras.

## 5. Inicio y revisión de healthchecks
Para levantar el entorno, ejecuta:
```bash
docker compose --env-file .env.production up -d --build
```
Verifica que los contenedores estén saludables:
```bash
docker compose ps
```
Ambos contenedores (`framework_api_prod` y `framework_oracle_prod`) deben reportar el estado `(healthy)`. Oracle puede demorar entre 1 a 3 minutos en inicializar.

## 6. Creación del perfil Oracle interno
Una vez que ambos contenedores estén saludables:
1. Accede a la interfaz web (ver configuración de HTTPS y dominio).
2. Ve a la sección "Perfiles de Conexión".
3. Crea un nuevo perfil. En el campo Host, ingresa el nombre de servicio interno de Docker: `oracle_db`.
4. El puerto es `1521` y el Service Name es `FREEPDB1` o el valor que hayas configurado en el entorno.

## 7. Configuración de HTTPS y Dominio
Para exponer la aplicación de manera segura, se recomienda utilizar un proxy reverso (como Nginx, Caddy o Traefik) frente al puerto `8000` de la API, encargándose de la terminación TLS (HTTPS). No modifiques puertos ni DNS sin autorización.
*Nota: El puerto 1521 de Oracle NO debe exponerse públicamente. La API se comunica a través de la red interna de Docker.*

## 8. Respaldo de volúmenes (Backup)
Los datos de la base de datos interna y de Oracle residen en volúmenes persistentes. Para respaldarlos:
```bash
# Detener los contenedores temporalmente
docker compose down
# Respaldar la carpeta de volúmenes de Docker (por defecto en /var/lib/docker/volumes/)
# o mediante un contenedor tar:
docker run --rm -v framework_pruebas_sql_framework_data:/data -v $(pwd):/backup ubuntu tar cvf /backup/framework_backup.tar /data
docker run --rm -v framework_pruebas_sql_oracle_data:/opt/oracle/oradata -v $(pwd):/backup ubuntu tar cvf /backup/oracle_backup.tar /opt/oracle/oradata
# Reiniciar los servicios
docker compose --env-file .env.production up -d
```

## 9. Actualización sin destruir datos
Para actualizar la aplicación sin perder información:
```bash
git pull origin fase-4-2-despliegue
docker compose --env-file .env.production build api
docker compose --env-file .env.production up -d --no-deps api
```

## 10. Rollback de una versión de la aplicación
Si la nueva versión de la imagen de la API presenta problemas, puedes volver a la versión anterior usando el tag de la imagen previa:
```bash
docker tag framework_pruebas_sql:version_anterior framework-pruebas-sql:fase-4-2
docker compose --env-file .env.production up -d --no-deps api
```
*Si hubo cambios en las migraciones, un rollback requerirá `alembic downgrade` de forma manual dentro del contenedor antes de reemplazar la imagen.*

## 11. Consulta segura de logs
Para revisar la actividad o diagnosticar errores sin exponer secretos:
```bash
docker compose logs api
docker compose logs oracle_db
```

## 12. Detención controlada sin eliminar volúmenes
Para apagar los servicios sin perder los datos:
```bash
docker compose down
```
**NUNCA** ejecutes `docker compose down -v` en producción a menos que desees destruir intencionadamente todas las bases de datos y su información permanentemente.
