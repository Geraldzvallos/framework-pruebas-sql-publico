import urllib.request
import urllib.error
import json
import base64
import os
import os

def read_env(filepath):
    d = {}
    with open(filepath) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                d[k] = v
    return d

env_vars = read_env('.env.oracle')
test_pwd = env_vars.get('FRAMEWORK_TEST_PASSWORD', 'test')

BASE_URL = "http://127.0.0.1:8000/api"

print("--- FLUJO FUNCIONAL REAL ORACLE ---")

def do_req(url, method="GET", data=None, auth=None):
    req = urllib.request.Request(BASE_URL + url, method=method)
    if data:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(data).encode('utf-8')
    if auth:
        creds = f"{auth[0]}:{auth[1]}"
        b64_creds = base64.b64encode(creds.encode('utf-8')).decode('ascii')
        req.add_header('Authorization', f'Basic {b64_creds}')
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

# 1. AUTENTICACIÓN
status, out = do_req("/projects/")
print(f"[AUTH] Sin credenciales: Status {status} (Espera 401)")

auth = ('admin', 'admin')

status, projects = do_req("/projects/", auth=auth)
print(f"[AUTH] Con credenciales: Status {status} (Espera 200)")
proj_id = projects[0]['id'] if isinstance(projects, list) and projects else 1

# Creamos perfil REAL Oracle
conn_payload = {
    "project_id": proj_id,
    "name": "Prueba Real Oracle",
    "engine": "ORACLE",
    "host": "127.0.0.1",
    "port": 1521,
    "username": "FRAMEWORK_TEST",
    "service_name": "FREEPDB1"
}
_, c_data = do_req("/connections/", method="POST", data=conn_payload, auth=auth)
conn_id = c_data['id']
exec_payload = {"connection_profile_id": conn_id, "password": test_pwd}

# 1. SELECT PASS
c_pass = {"project_id": proj_id, "name": "PASS", "sql_query": "SELECT 1 FROM DUAL", "validation_type": "ROW_COUNT", "expected_result": "1"}
_, c1 = do_req("/test-cases/", method="POST", data=c_pass, auth=auth)
_, e1 = do_req(f"/execute/test-case/{c1['id']}", method="POST", data=exec_payload, auth=auth)
print(f"[SELECT PASS] Status: {e1.get('status')} - Actual: {e1.get('actual_result')}")

# 2. SELECT FAIL
c_fail = {"project_id": proj_id, "name": "FAIL", "sql_query": "SELECT 1 FROM DUAL", "validation_type": "ROW_COUNT", "expected_result": "99"}
_, c2 = do_req("/test-cases/", method="POST", data=c_fail, auth=auth)
_, e2 = do_req(f"/execute/test-case/{c2['id']}", method="POST", data=exec_payload, auth=auth)
print(f"[SELECT FAIL] Status: {e2.get('status')} - Actual: {e2.get('actual_result')}")

# 3. SELECT ERROR
c_err = {"project_id": proj_id, "name": "ERROR", "sql_query": "SELECT * FROM INEXISTENTE", "validation_type": "EXISTS", "expected_result": "true"}
_, c3 = do_req("/test-cases/", method="POST", data=c_err, auth=auth)
_, e3 = do_req(f"/execute/test-case/{c3['id']}", method="POST", data=exec_payload, auth=auth)
print(f"[SELECT ERROR] Status: {e3.get('status')} - Msj: {e3.get('error_message')[:50]}")

# 4. DML ROLLBACK
c_dml = {"project_id": proj_id, "name": "DML", "sql_query": "INSERT INTO FRAMEWORK_TEST_ITEMS (ID, NAME, ACTIVE) VALUES (100, 'Test', 1)", "validation_type": "ROW_COUNT", "expected_result": "1"}
_, c4 = do_req("/test-cases/", method="POST", data=c_dml, auth=auth)
_, e4 = do_req(f"/execute/test-case/{c4['id']}", method="POST", data=exec_payload, auth=auth)
print(f"[DML ROLLBACK] Status: {e4.get('status')} - Rollback: {e4.get('rollback_applied')}")

# 5. SUITE
s_pay = {"project_id": proj_id, "name": "Suite", "description": "Desc"}
_, s = do_req("/suites/", method="POST", data=s_pay, auth=auth)
do_req(f"/suites/{s['id']}/test-cases/{c1['id']}", method="POST", auth=auth)
do_req(f"/suites/{s['id']}/test-cases/{c2['id']}", method="POST", auth=auth)
do_req(f"/suites/{s['id']}/test-cases/{c3['id']}", method="POST", auth=auth)
_, se = do_req(f"/execute/suite/{s['id']}", method="POST", data=exec_payload, auth=auth)
print(f"[SUITE EXEC] Total: {se.get('total_tests')} | PASS: {se.get('passed')} | FAIL: {se.get('failed')} | ERRORS: {se.get('errors')}")

# 6. Historial paginación
_, h = do_req("/history/?limit=3&skip=0", auth=auth)
print(f"[HISTORIAL] Recuperados {len(h)} registros usando limit=3.")

print("--- FIN FLUJO ---")
