from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, Any, List
from datetime import datetime
from enum import Enum


class ValidationTypeEnum(str, Enum):
    ROW_COUNT = "ROW_COUNT"
    EXISTS = "EXISTS"

class EnvironmentTypeEnum(str, Enum):
    TEST = "TEST"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


# --- ESQUEMAS DE PROYECTOS ---

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre del proyecto no puede estar vacío ni contener solo espacios.")
        return v

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("El nombre del proyecto no puede estar vacío.")
        return v

class ProjectResponse(ProjectCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- ESQUEMAS DE PERFILES DE CONEXIÓN ---

class ConnectionProfileCreate(BaseModel):
    project_id: int
    name: str = Field(..., min_length=1, max_length=100)
    engine: str = Field("ORACLE", min_length=1, max_length=20)
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(1521, ge=1, le=65535)
    service_name: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., min_length=1, max_length=100)
    environment_type: EnvironmentTypeEnum = EnvironmentTypeEnum.TEST

    @field_validator('name', 'host', 'service_name', 'username')
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El campo no puede estar vacío ni contener solo espacios.")
        return v

    @field_validator('engine')
    @classmethod
    def validate_engine(cls, v: str) -> str:
        v = v.strip().upper()
        if v != 'ORACLE':
            raise ValueError("El único motor soportado es ORACLE.")
        return v

class ConnectionProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    host: Optional[str] = Field(None, min_length=1, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    service_name: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=1, max_length=100)
    environment_type: Optional[EnvironmentTypeEnum] = None

    @field_validator('name', 'host', 'service_name', 'username')
    @classmethod
    def validate_non_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("El campo no puede estar vacío ni contener solo espacios.")
        return v

class ConnectionProfileResponse(BaseModel):
    id: int
    project_id: int
    name: str
    engine: str
    host: str
    port: int
    service_name: str
    username: str
    environment_type: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TestConnectionRequest(BaseModel):
    password: str = Field(..., min_length=1)


# --- ESQUEMAS DE CASOS DE PRUEBA ---

class TestCaseCreate(BaseModel):
    project_id: Optional[int] = 1
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    sql_query: str = Field(..., min_length=1)
    validation_type: ValidationTypeEnum = ValidationTypeEnum.ROW_COUNT
    expected_result: str = Field(..., min_length=1)

    @field_validator('name', 'sql_query', 'expected_result')
    @classmethod
    def validate_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El campo no puede estar vacío ni contener solo espacios.")
        return v

    @field_validator('expected_result')
    @classmethod
    def validate_expected(cls, v: str, info) -> str:
        raw_val_type = info.data.get('validation_type', ValidationTypeEnum.ROW_COUNT)
        val_type_str = str(getattr(raw_val_type, 'value', raw_val_type)).upper()
        clean_v = v.strip()

        if val_type_str == "ROW_COUNT":
            try:
                val = int(clean_v)
                if val < 0:
                    raise ValueError("Para ROW_COUNT el resultado esperado debe ser un número entero mayor o igual a 0.")
            except ValueError:
                raise ValueError("Para ROW_COUNT el resultado esperado debe ser un número entero válido (>= 0).")
        elif val_type_str == "EXISTS":
            if clean_v.upper() not in {"TRUE", "FALSE"}:
                raise ValueError("Para EXISTS el resultado esperado debe ser 'true' o 'false'.")
            clean_v = clean_v.lower()
        return clean_v


class TestCaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    sql_query: Optional[str] = Field(None, min_length=1)
    validation_type: Optional[ValidationTypeEnum] = None
    expected_result: Optional[str] = Field(None, min_length=1)

    @field_validator('name', 'sql_query')
    @classmethod
    def validate_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("El campo no puede estar vacío ni contener solo espacios.")
        return v

class TestCaseResponse(TestCaseCreate):
    id: int
    project_id: int
    model_config = ConfigDict(from_attributes=True)


# --- ESQUEMAS DE SUITES DE PRUEBAS ---

class TestSuiteCreate(BaseModel):
    project_id: Optional[int] = 1
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre de la suite no puede estar vacío.")
        return v

class TestSuiteUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("El nombre de la suite no puede estar vacío.")
        return v

class TestSuiteResponse(TestSuiteCreate):
    id: int
    project_id: int
    test_cases: List[TestCaseResponse] = []
    model_config = ConfigDict(from_attributes=True)


# --- ESQUEMAS DEL MOTOR DE EJECUCIÓN ---

class DBCredentials(BaseModel):
    dsn: Optional[str] = None
    user: Optional[str] = None
    password: str
    connection_profile_id: Optional[int] = None
    environment_type: EnvironmentTypeEnum = EnvironmentTypeEnum.PRODUCTION
    confirm_staging_dml: bool = False

class ExecutionRequest(DBCredentials):
    sql_query: str

class TestCaseExecutionRequest(DBCredentials):
    pass

class SuiteExecutionRequest(DBCredentials):
    pass

class ExecutionResponse(BaseModel):
    success: bool
    statement_type: str = "UNKNOWN"
    rows: List[Any] = []
    rowcount: int = 0
    data: List[Any] = []
    message: str
    error_message: Optional[str] = None
    rollback_applied: bool = False
    rollback_error: Optional[str] = None


# --- ESQUEMAS DEL HISTORIAL DE EJECUCIONES ---

class HistoryResponse(BaseModel):
    id: int
    project_id: int
    test_case_id: Optional[int] = None
    suite_id: Optional[int] = None
    connection_profile_id: Optional[int] = None
    status: str
    executed_at: datetime
    duration_ms: float
    statement_type: Optional[str] = None
    executed_sql: str
    validation_type: Optional[str] = None
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    rowcount: int = 0
    rollback_applied: bool = False
    rollback_error: Optional[str] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SuiteExecutionSummary(BaseModel):
    suite_id: int
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    errors: int
    total_duration_ms: float
    details: List[HistoryResponse] = []
