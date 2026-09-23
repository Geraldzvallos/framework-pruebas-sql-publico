# Instalación Local

## Requisitos
- Python 3.9+
- Motor de Base de Datos SQLite (Incluido) o Cliente de Oracle DB.

## Instrucciones
1. Clonar el repositorio.
2. Crear un entorno virtual: `python -m venv venv`.
3. Activar el entorno virtual: `.\venv\Scripts\Activate` (Windows) o `source venv/bin/activate` (Linux/Mac).
4. Instalar dependencias: `pip install -r requirements.txt`.
5. Copiar `.env.example` a `.env` y ajustar variables.
6. Aplicar migraciones: `alembic upgrade head`.
7. Iniciar el servidor local: `uvicorn app.main:app --reload`.
