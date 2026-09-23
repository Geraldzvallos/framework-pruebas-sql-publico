import urllib.request
import urllib.error
import json
import base64
import os
import sys
import uuid

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

has_error = False
conn_id = None
c1_id = None
c2_id = None
c3_id = None
c4_id = None
s_id = None

run_id = str(uuid.uuid4())[:8]

try:
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

    # Creamos perfil REAL Oracle
    conn_payload = {
        "project_id": proj_id,
        "name": f"Prueba Real Oracle {run_id}",
        "engine": "ORACLE",
        "host": "127.0.0.1",
        "port": 1521,
        "username": "FRAMEWORK_TEST",
        "service_name": "FREEPDB1"
    }
    s_c, c_data = do_req("/connections/", method="POST", data=conn_payload, auth=auth)
    if s_c not in (200, 201) or 'id' not in c_data:
        print(f"ERROR creando conexión. Status: {s_c}")
        sys.exit(1)
    conn_id = c_data['id']

    exec_payload = {"connection_profile_id": conn_id, "password": test_pwd}

    # 1. SELECT PASS
    c_pass = {"project_id": proj_id, "name": f"PASS {run_id}", "sql_query": "SELECT 1 FROM DUAL", "validation_type": "ROW_COUNT", "expected_result": "1"}
    s_c1, c1 = do_req("/test-cases/", method="POST", data=c_pass, auth=auth)
    if s_c1 not in (200, 201) or 'id' not in c1:
        print(f"ERROR creando SELECT PASS. Status: {s_c1}")
        has_error = True
    else:
        c1_id = c1['id']
        s_e1, e1 = do_req(f"/execute/test-case/{c1_id}", method="POST", data=exec_payload, auth=auth)
        if s_e1 == 200:
            print(f"[SELECT PASS] Status: {e1.get('status')} - Actual: {e1.get('actual_result')}")
        else:
            print(f"Error ejecutando SELECT PASS: {e1}")
            has_error = True

    # 2. SELECT FAIL
    c_fail = {"project_id": proj_id, "name": f"FAIL {run_id}", "sql_query": "SELECT 1 FROM DUAL", "validation_type": "ROW_COUNT", "expected_result": "99"}
    s_c2, c2 = do_req("/test-cases/", method="POST", data=c_fail, auth=auth)
    if s_c2 not in (200, 201) or 'id' not in c2:
        print(f"ERROR creando SELECT FAIL. Status: {s_c2}")
        has_error = True
    else:
        c2_id = c2['id']
        s_e2, e2 = do_req(f"/execute/test-case/{c2_id}", method="POST", data=exec_payload, auth=auth)
        if s_e2 == 200:
            print(f"[SELECT FAIL] Status: {e2.get('status')} - Actual: {e2.get('actual_result')}")
        else:
            has_error = True

    # 3. SELECT ERROR
    c_err = {"project_id": proj_id, "name": f"ERROR {run_id}", "sql_query": "SELECT * FROM INEXISTENTE", "validation_type": "EXISTS", "expected_result": "true"}
    s_c3, c3 = do_req("/test-cases/", method="POST", data=c_err, auth=auth)
    if s_c3 not in (200, 201) or 'id' not in c3:
        print(f"ERROR creando SELECT ERROR. Status: {s_c3}")
        has_error = True
    else:
        c3_id = c3['id']
        s_e3, e3 = do_req(f"/execute/test-case/{c3_id}", method="POST", data=exec_payload, auth=auth)
        if s_e3 == 200:
            print(f"[SELECT ERROR] Status: {e3.get('status')} - Msj: {str(e3.get('error_message'))[:50]}")
        else:
            has_error = True

    # 4. DML ROLLBACK
    c_dml = {"project_id": proj_id, "name": f"DML {run_id}", "sql_query": "INSERT INTO FRAMEWORK_TEST_ITEMS (ID, NAME, ACTIVE) VALUES (100, 'Test', 1)", "validation_type": "ROW_COUNT", "expected_result": "1"}
    s_c4, c4 = do_req("/test-cases/", method="POST", data=c_dml, auth=auth)
    if s_c4 not in (200, 201) or 'id' not in c4:
        print(f"ERROR creando DML ROLLBACK. Status: {s_c4}")
        has_error = True
    else:
        c4_id = c4['id']
        s_e4, e4 = do_req(f"/execute/test-case/{c4_id}", method="POST", data=exec_payload, auth=auth)
        if s_e4 == 200:
            print(f"[DML ROLLBACK] Status: {e4.get('status')} - Rollback: {e4.get('rollback_applied')}")
        else:
            has_error = True

    # 5. SUITE
    if c1_id and c2_id and c3_id:
        s_pay = {"project_id": proj_id, "name": f"Suite {run_id}", "description": "Desc"}
        s_ss, s = do_req("/suites/", method="POST", data=s_pay, auth=auth)
        if s_ss in (200, 201) and 'id' in s:
            s_id = s['id']
            do_req(f"/suites/{s_id}/test-cases/{c1_id}", method="POST", auth=auth)
            do_req(f"/suites/{s_id}/test-cases/{c2_id}", method="POST", auth=auth)
            do_req(f"/suites/{s_id}/test-cases/{c3_id}", method="POST", auth=auth)
            s_se, se = do_req(f"/execute/suite/{s_id}", method="POST", data=exec_payload, auth=auth)
            if s_se == 200:
                print(f"[SUITE EXEC] Total: {se.get('total_tests')} | PASS: {se.get('passed')} | FAIL: {se.get('failed')} | ERRORS: {se.get('errors')}")
            else:
                has_error = True
        else:
            has_error = True

    # 6. Historial paginación
    s_h, h = do_req("/history/?limit=3&skip=0", auth=auth)
    if s_h == 200:
        if isinstance(h, list):
            print(f"[HISTORIAL] Recuperados {len(h)} registros usando limit=3.")
        else:
            print(f"[HISTORIAL] Recuperados {len(h.get('items', []))} registros usando limit=3.")
    else:
        has_error = True

finally:
    print("--- LIMPIEZA ---")
    if conn_id:
        do_req(f"/connections/{conn_id}", method="DELETE", auth=auth)
    if s_id:
        do_req(f"/suites/{s_id}", method="DELETE", auth=auth)
    if c1_id:
        do_req(f"/test-cases/{c1_id}", method="DELETE", auth=auth)
    if c2_id:
        do_req(f"/test-cases/{c2_id}", method="DELETE", auth=auth)
    if c3_id:
        do_req(f"/test-cases/{c3_id}", method="DELETE", auth=auth)
    if c4_id:
        do_req(f"/test-cases/{c4_id}", method="DELETE", auth=auth)
    print("--- FIN FLUJO ---")

if has_error:
    sys.exit(1)
