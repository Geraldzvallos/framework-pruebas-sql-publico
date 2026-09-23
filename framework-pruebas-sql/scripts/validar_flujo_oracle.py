import urllib.request
import urllib.error
import json
import base64
import os
import sys

def read_env(filepath):
    d = {}
    if not os.path.exists(filepath):
        return d
    with open(filepath) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                d[k] = v
    return d

env_vars = read_env('.env.oracle')
test_pwd = env_vars.get('FRAMEWORK_TEST_PASSWORD') or os.getenv('FRAMEWORK_TEST_PASSWORD')
auth_user = env_vars.get('APP_ACCESS_USERNAME') or os.getenv('APP_ACCESS_USERNAME')
auth_pwd = env_vars.get('APP_ACCESS_PASSWORD') or os.getenv('APP_ACCESS_PASSWORD')

if not all([test_pwd, auth_user, auth_pwd]):
    print("ERROR: Faltan variables de entorno obligatorias (APP_ACCESS_USERNAME, APP_ACCESS_PASSWORD, FRAMEWORK_TEST_PASSWORD).")
    print("Configure .env.oracle o expórtelas en el entorno antes de ejecutar este script.")
    sys.exit(1)

auth = (auth_user, auth_pwd)

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
        body = e.read().decode('utf-8')
        try:
            return e.code, json.loads(body)
        except:
            return e.code, body

# 1. AUTENTICACIÓN
status, out = do_req("/projects/")
print(f"[AUTH] Sin credenciales: Status {status} (Espera 401)")
if status != 401:
    print("ERROR FATAL: La aplicación no requirió autenticación.")
    sys.exit(1)

status, projects = do_req("/projects/", auth=auth)
print(f"[AUTH] Con credenciales: Status {status} (Espera 200)")
if status != 200:
    print("ERROR FATAL: Autenticación fallida con las credenciales proporcionadas.")
    sys.exit(1)

proj_id = projects[0]['id'] if isinstance(projects, list) and projects else 1

# Limpieza previa de posibles datos de ejecuciones anteriores (si procede)
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
s_c, c_data = do_req("/connections/", method="POST", data=conn_payload, auth=auth)
if s_c not in (200, 201):
    print("ERROR creando conexión.")
    sys.exit(1)

conn_id = c_data['id']
exec_payload = {"connection_profile_id": conn_id, "password": test_pwd}

# 1. SELECT PASS
c_pass = {"project_id": proj_id, "name": "PASS", "sql_query": "SELECT 1 FROM DUAL", "validation_type": "ROW_COUNT", "expected_result": "1"}
_, c1 = do_req("/test-cases/", method="POST", data=c_pass, auth=auth)
s_e1, e1 = do_req(f"/execute/test-case/{c1['id']}", method="POST", data=exec_payload, auth=auth)
if s_e1 == 200:
    print(f"[SELECT PASS] Status: {e1.get('status')} - Actual: {e1.get('actual_result')}")
else:
    print(f"Error ejecutando SELECT PASS: {e1}")

# 2. SELECT FAIL
c_fail = {"project_id": proj_id, "name": "FAIL", "sql_query": "SELECT 1 FROM DUAL", "validation_type": "ROW_COUNT", "expected_result": "99"}
_, c2 = do_req("/test-cases/", method="POST", data=c_fail, auth=auth)
s_e2, e2 = do_req(f"/execute/test-case/{c2['id']}", method="POST", data=exec_payload, auth=auth)
if s_e2 == 200:
    print(f"[SELECT FAIL] Status: {e2.get('status')} - Actual: {e2.get('actual_result')}")

# 3. SELECT ERROR
c_err = {"project_id": proj_id, "name": "ERROR", "sql_query": "SELECT * FROM INEXISTENTE", "validation_type": "EXISTS", "expected_result": "true"}
_, c3 = do_req("/test-cases/", method="POST", data=c_err, auth=auth)
s_e3, e3 = do_req(f"/execute/test-case/{c3['id']}", method="POST", data=exec_payload, auth=auth)
if s_e3 == 200:
    print(f"[SELECT ERROR] Status: {e3.get('status')} - Msj: {str(e3.get('error_message'))[:50]}")

# 4. DML ROLLBACK
c_dml = {"project_id": proj_id, "name": "DML", "sql_query": "INSERT INTO FRAMEWORK_TEST_ITEMS (ID, NAME, ACTIVE) VALUES (100, 'Test', 1)", "validation_type": "ROW_COUNT", "expected_result": "1"}
_, c4 = do_req("/test-cases/", method="POST", data=c_dml, auth=auth)
s_e4, e4 = do_req(f"/execute/test-case/{c4['id']}", method="POST", data=exec_payload, auth=auth)
if s_e4 == 200:
    print(f"[DML ROLLBACK] Status: {e4.get('status')} - Rollback: {e4.get('rollback_applied')}")

# 5. SUITE
s_pay = {"project_id": proj_id, "name": "Suite", "description": "Desc"}
_, s = do_req("/suites/", method="POST", data=s_pay, auth=auth)
do_req(f"/suites/{s['id']}/test-cases/{c1['id']}", method="POST", auth=auth)
do_req(f"/suites/{s['id']}/test-cases/{c2['id']}", method="POST", auth=auth)
do_req(f"/suites/{s['id']}/test-cases/{c3['id']}", method="POST", auth=auth)
s_se, se = do_req(f"/execute/suite/{s['id']}", method="POST", data=exec_payload, auth=auth)
if s_se == 200:
    print(f"[SUITE EXEC] Total: {se.get('total_tests')} | PASS: {se.get('passed')} | FAIL: {se.get('failed')} | ERRORS: {se.get('errors')}")

# 6. Historial paginación
s_h, h = do_req("/history/?limit=3&skip=0", auth=auth)
if s_h == 200:
    print(f"[HISTORIAL] Recuperados {len(h.get('items', []))} registros usando limit=3.")

# Limpieza (opcional)
do_req(f"/connections/{conn_id}", method="DELETE", auth=auth)
do_req(f"/suites/{s['id']}", method="DELETE", auth=auth)
do_req(f"/test-cases/{c1['id']}", method="DELETE", auth=auth)
do_req(f"/test-cases/{c2['id']}", method="DELETE", auth=auth)
do_req(f"/test-cases/{c3['id']}", method="DELETE", auth=auth)
do_req(f"/test-cases/{c4['id']}", method="DELETE", auth=auth)

print("--- FIN FLUJO ---")
