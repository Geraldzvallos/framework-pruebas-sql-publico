# Manual Técnico

## Configuración del Entorno de Desarrollo Local

1. **Requisitos Previos**
   - Python 3.12+
   - Node.js (solo para validaciones de sintaxis frontend, el frontend en sí no requiere compilación).
   - Docker y Docker Compose (opcional pero recomendado para probar con Oracle).

2. **Instalación**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Variables de Entorno**
   Copiar `.env.example` a `.env` y ajustar según sea necesario.
   ```properties
   API_HOST=0.0.0.0
   API_PORT=8000
   FRAMEWORK_DB_URL=sqlite:///./framework_interno.db
   APP_ACCESS_ENABLED=false
   RUN_ORACLE_TESTS=0
   ```

4. **Migraciones**
   La base de datos SQLite se crea automáticamente. Si hay cambios en los modelos de SQLAlchemy, genere una migración:
   ```powershell
   alembic revision --autogenerate -m "Mensaje"
   alembic upgrade head
   ```

5. **Ejecución del Servidor**
   ```powershell
   uvicorn app.main:app --reload
   ```
   La interfaz gráfica (frontend) será servida automáticamente en `http://127.0.0.1:8000/ui/`.
   La documentación OpenAPI (Swagger) estará disponible en `http://127.0.0.1:8000/docs`.

## Ejecución de Pruebas Automáticas

El conjunto de pruebas unitarias y de integración se ha diseñado utilizando Pytest.

**Pruebas base (sin Oracle)**:
Configuran una base de datos SQLite efímera (`sqlite:///:memory:`) utilizando un pool estático para garantizar la inmutabilidad de la base local durante las pruebas.
```powershell
pytest -q -m "not oracle_integration"
```

**Pruebas con Oracle Real**:
Para validar la comunicación con Oracle, levante primero el contenedor (`docker compose up -d`) y establezca las variables en `.env.oracle` (copiado desde `.env.oracle.example`). Luego ejecute:
```powershell
pytest -q -m oracle_integration
```

## Empaquetado Seguro
Existe un script `scripts/build_clean_zip.py` que se encarga de crear un archivo `.zip` con el código fuente excluyendo directorios y archivos sensibles (bases de datos locales `.db`, entornos virtuales, secretos, y subdirectorios de Git).
```powershell
python scripts/build_clean_zip.py
```

## Respaldo y Restauración de SQLite (Vía Docker)
Si el sistema corre bajo Docker y se desea respaldar la metadata:
```bash
docker cp framework_api_prod:/data/framework_interno.db framework_interno_backup.db
```
Para restaurar, copie el archivo al volumen correspondiente.
