import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env antes de cualquier otra importación
load_dotenv()

import secrets
import base64
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.database import engine, Base, SessionLocal
from app.models import project, connection, test_case, suite, history
from app.api import projects, connections, test_cases, suites, executions, history as api_history
# La creación del esquema y el Proyecto general se delega a las migraciones de Alembic (alembic upgrade head).

app = FastAPI(
    title="Framework de Pruebas SQL",
    description="API para ejecución, validación y trazabilidad de pruebas en bases de datos relacionales (Oracle MVP).",
    version="2.0.0"
)

# Configuración CORS centralizada mediante variable de entorno
cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost,http://localhost:3000,http://127.0.0.1,http://127.0.0.1:3000")
origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]

# Si permitimos "*", las credenciales deben desactivarse por seguridad y compatibilidad
allow_creds = "*" not in origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def basic_auth_middleware(request: Request, call_next):
    # Solo aplicar protección si está habilitada en entorno
    if not os.getenv("APP_ACCESS_ENABLED", "").lower() == "true":
        return await call_next(request)
        
    # Rutas públicas (healthcheck y quizás archivos estáticos si fuera el caso, pero pide proteger /ui/)
    if request.url.path == "/" or request.url.path == "/health":
        return await call_next(request)
        
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"}, headers={"WWW-Authenticate": "Basic"})
        
    try:
        decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"}, headers={"WWW-Authenticate": "Basic"})
        
    expected_username = os.getenv("APP_ACCESS_USERNAME", "")
    expected_password = os.getenv("APP_ACCESS_PASSWORD", "")
    
    is_username_correct = secrets.compare_digest(username, expected_username)
    is_password_correct = secrets.compare_digest(password, expected_password)
    
    if not (is_username_correct and is_password_correct):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"}, headers={"WWW-Authenticate": "Basic"})
        
    return await call_next(request)

# Registro de routers de la API v2
app.include_router(projects.router, prefix="/api", tags=["Proyectos"])
app.include_router(connections.router, prefix="/api", tags=["Perfiles de Conexión"])
app.include_router(test_cases.router, prefix="/api", tags=["Casos de Prueba"])
app.include_router(suites.router, prefix="/api", tags=["Suites de Pruebas"])
app.include_router(executions.router, prefix="/api", tags=["Motor de Ejecución"])
app.include_router(api_history.router, prefix="/api", tags=["Historial de Ejecuciones"])

# Montar frontend en /ui/
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/ui", StaticFiles(directory=frontend_path, html=True), name="ui")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "El motor del Framework SQL está en línea.", "version": "2.0.0"}