# Respaldo y Restauración

## Respaldo de framework_interno.db
El motor principal guarda perfiles, historiales y suites en `framework_interno.db` (SQLite).
Para realizar un respaldo seguro:
```bash
python scripts/backup_db.py
```
O simplemente realice una copia física del archivo:
```bash
cp framework_interno.db framework_interno.db.bak
```

## Restauración
Para restaurar, detenga el proceso FastAPI y reemplace el archivo:
```bash
mv framework_interno.db.bak framework_interno.db
```
