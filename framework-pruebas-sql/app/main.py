import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env antes de cualquier otra importación
load_dotenv()

import secrets
import base64
import hmac
import hashlib
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
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

def create_session_token():
    secret = os.getenv("APP_SESSION_SECRET", "default_insecure_secret").encode()
    token_data = b"auth_valid"
    signature = hmac.new(secret, token_data, hashlib.sha256).hexdigest()
    return f"auth_valid.{signature}"

def verify_session_token(token: str):
    if not token or not token.startswith("auth_valid."):
        return False
    secret = os.getenv("APP_SESSION_SECRET", "default_insecure_secret").encode()
    expected_signature = hmac.new(secret, b"auth_valid", hashlib.sha256).hexdigest()
    try:
        _, signature = token.split(".", 1)
        return secrets.compare_digest(signature, expected_signature)
    except ValueError:
        return False

@app.middleware("http")
async def cookie_auth_middleware(request: Request, call_next):
    # Solo aplicar protección si está habilitada en entorno
    if not os.getenv("APP_ACCESS_ENABLED", "").lower() == "true":
        return await call_next(request)

    expected_username = os.getenv("APP_ACCESS_USERNAME", "").strip()
    expected_password = os.getenv("APP_ACCESS_PASSWORD", "").strip()
    if not expected_username or not expected_password:
        return JSONResponse(status_code=503, content={"detail": "Service Unavailable: Incomplete configuration"})

    path = request.url.path

    # Rutas públicas
    if path in ["/", "/health", "/login", "/api/login"]:
        return await call_next(request)

    # Rutas de frontend de assets (css, js, imágenes) permitidas sin auth para cargar el login
    if path.startswith("/ui/css/") or path.startswith("/ui/js/"):
        return await call_next(request)

    session_token = request.cookies.get("session_token")
    if not verify_session_token(session_token):
        if path.startswith("/api/"):
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        else:
            return RedirectResponse(url="/login", status_code=303)

    return await call_next(request)

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login", tags=["Autenticación"])
def login(creds: LoginRequest):
    expected_username = os.getenv("APP_ACCESS_USERNAME", "").strip()
    expected_password = os.getenv("APP_ACCESS_PASSWORD", "").strip()

    if not secrets.compare_digest(creds.username, expected_username) or \
       not secrets.compare_digest(creds.password, expected_password):
        return JSONResponse(status_code=401, content={"detail": "Credenciales inválidas"})

    token = create_session_token()
    response = JSONResponse(content={"detail": "Login exitoso"})
    secure_cookie = os.getenv("ENVIRONMENT", "production").lower() == "production"
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=86400
    )
    return response

@app.post("/api/logout", tags=["Autenticación"])
def logout():
    response = JSONResponse(content={"detail": "Logout exitoso"})
    response.delete_cookie("session_token")
    return response

@app.get("/login", include_in_schema=False)
def get_login_page():
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
    login_html = os.path.join(frontend_path, "login.html")
    if os.path.exists(login_html):
        return FileResponse(login_html)
    return JSONResponse(status_code=404, content={"detail": "login.html not found"})

@app.get("/health", tags=["Salud"])
def health_check():
    return {"status": "ok", "message": "El motor del Framework SQL está en línea.", "version": "2.0.0"}

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