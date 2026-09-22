import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_frontend_connection_profile_contract():
    # Simula el JSON exacto que enviará el frontend para crear un perfil
    payload = {
        "project_id": 1,
        "name": "Prueba Frontend",
        "engine": "oracle",
        "host": "localhost",
        "port": 1521,
        "service_name": "xe",
        "username": "sys"
    }
    # En la fase 2.1 un proyecto 1 se crea automáticamente si está la migración, o podemos intentar crear uno si falla
    res_proj = client.post("/api/projects/", json={"name": "Fase 3.1", "description": ""})
    proj_id = res_proj.json()["id"] if res_proj.status_code == 201 else 1

    payload["project_id"] = proj_id
    
    res = client.post("/api/connections/", json=payload)
    assert res.status_code == 201, f"Fallo al crear perfil: {res.text}"
    
    # Confirmar que en la lista viene el campo 'name' y 'service_name'
    res_list = client.get(f"/api/connections/?project_id={proj_id}")
    assert res_list.status_code == 200
    conns = res_list.json()
    assert len(conns) > 0
    assert "name" in conns[-1]
    assert "profile_name" not in conns[-1]
    assert "sid" not in conns[-1]
    
    # Probar endpoint de PUT (Edición)
    conn_id = conns[-1]["id"]
    payload["name"] = "Editado"
    res_put = client.put(f"/api/connections/{conn_id}", json=payload)
    assert res_put.status_code == 200

def test_frontend_suite_execution_contract():
    # Crear un proyecto y conexión
    res_proj = client.post("/api/projects/", json={"name": "Proj Suite", "description": ""})
    proj_id = res_proj.json()["id"] if res_proj.status_code == 201 else 1
    
    res_conn = client.post("/api/connections/", json={
        "project_id": proj_id, "name": "Conn", "engine": "oracle", 
        "host": "loc", "port": 1521, "service_name": "xe", "username": "u"
    })
    conn_id = res_conn.json()["id"]
    
    # Crear un caso de prueba
    res_case = client.post("/api/test-cases/", json={
        "project_id": proj_id,
        "name": "C1",
        "sql_query": "SELECT 1 FROM DUAL",
        "validation_type": "ROW_COUNT",
        "expected_result": "1"
    })
    case_id = res_case.json()["id"]
    
    # Crear suite
    res_suite = client.post("/api/suites/", json={"project_id": proj_id, "name": "S1"})
    suite_id = res_suite.json()["id"]
    
    # Asociar
    res_assoc = client.post(f"/api/suites/{suite_id}/test-cases/{case_id}")
    assert res_assoc.status_code == 200
    
    # Ejecutar suite simulada
    res_exec = client.post(f"/api/execute/suite/{suite_id}", json={
        "connection_profile_id": conn_id,
        "password": "pwd"
    })
    assert res_exec.status_code == 200
    data = res_exec.json()
    
    # Validar el contrato consumido por app.js
    assert "total_tests" in data
    assert "passed" in data
    assert "failed" in data
    assert "errors" in data
    assert "total_duration_ms" in data
    assert "details" in data
    assert isinstance(data["details"], list)

    assert "summary" not in data
    assert "results" not in data

def test_frontend_does_not_contain_old_contracts():
    # Leer app.js y asegurar que no hay referencias a profile_name o res.summary
    with open("frontend/app.js", "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "profile_name" not in content
    assert "res.summary" not in content
    assert "res.results" not in content
    assert "total_executed" not in content

def test_put_endpoints_available():
    # Probar que proyectos, perfiles, casos y suites tienen PUT 405 (si no está impl) o 422/200 (si está impl)
    # Ya probamos PUT de connection en el de connection. 
    # Validemos que existen (al menos devuelve 422 si body vacío, no 405)
    res_p = client.put("/api/projects/9999", json={})
    assert res_p.status_code != 405
    
    res_c = client.put("/api/test-cases/9999", json={})
    assert res_c.status_code != 405
    
    res_s = client.put("/api/suites/9999", json={})
    assert res_s.status_code != 405
