# Respaldo y Restauración

## Respaldo

El motor principal guarda perfiles, historiales y suites en `framework_interno.db` (SQLite). 
Para realizar un respaldo seguro, simplemente realice una copia física del archivo local:
```bash
cp framework_interno.db framework_interno_backup.db
```

Si está ejecutando el sistema mediante Docker, puede respaldar los datos del volumen persistente copiando el archivo desde el contenedor:
```bash
docker cp framework_api_prod:/data/framework_interno.db framework_interno_backup.db
```

## Restauración

Para restaurar de manera segura, es **obligatorio** realizar una detención controlada de la API antes de reemplazar el archivo, para evitar corrupción de datos.

1. Detenga el proceso de la API (por ejemplo, con `Ctrl+C` si usa uvicorn localmente, o `docker compose down` si usa Docker).
2. Reemplace el archivo de la base de datos con su respaldo:
```bash
# Restauración local
mv framework_interno_backup.db framework_interno.db
```
*(Si usa Docker, restaure iniciando un contenedor temporal o copiando de vuelta el archivo hacia el volumen/directorio montado).*
3. Vuelva a iniciar la API (`uvicorn app.main:app --reload` o `docker compose up -d`).
