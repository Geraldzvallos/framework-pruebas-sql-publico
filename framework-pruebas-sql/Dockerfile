FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY alembic/ ./alembic/
COPY app/ ./app/
COPY frontend/ ./frontend/
COPY scripts/start_production.sh ./scripts/

# Hacer el script ejecutable
RUN chmod +x ./scripts/start_production.sh

# Usuario no root (el ID debe poder escribir en /data, por lo que SQLite usa un volumen externo)
# Creamos el directorio data en caso de no usar volumen para pruebas simples
RUN mkdir -p /data && useradd -m appuser && chown -R appuser:appuser /app /data
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

CMD ["./scripts/start_production.sh"]
