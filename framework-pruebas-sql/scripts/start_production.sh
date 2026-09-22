#!/bin/bash
set -e

# Asegurar que el directorio de datos existe
mkdir -p /data

# Aplicar migraciones
echo "Aplicando migraciones..."
alembic upgrade head || { echo "Error aplicando migraciones"; exit 1; }

# Iniciar la aplicación
echo "Iniciando Uvicorn..."
exec uvicorn app.main:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000}
