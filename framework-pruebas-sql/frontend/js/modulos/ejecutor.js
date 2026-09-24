import { estado } from '../core/estado.js';
import { fetchAPI, handleAPIError } from '../core/api.js';
import { actualizarDatosProyectoActivo } from './dashboard.js';
import { escapeHTML } from '../core/utilidades.js';

let modalPwdInst = null;
let execAction = null;
let execTargetId = null;

export function getModalPwdInst() {
    if (!modalPwdInst) {
        modalPwdInst = new bootstrap.Modal(document.getElementById("modalPassword"));
    }
    return modalPwdInst;
}

export function abrirTestConexion(connId) {
    execAction = "TEST_CONN"; execTargetId = connId;
    document.getElementById("pwd-conn-select-container").classList.add("hidden");
    document.getElementById("pwd-password").value = "";
    document.getElementById("modalPasswordText").innerText = "Probar perfil de conexión #" + connId;
    getModalPwdInst().show();
}

export async function abrirEjecucion(type, targetId) {
    if (estado.conexiones.length === 0) { Swal.fire("Atención", "Cree un perfil de conexión primero.", "warning"); return; }
    execAction = type; execTargetId = targetId;
    const sel = document.getElementById("pwd-connection-id");
    sel.innerHTML = "";
    estado.conexiones.forEach(c => { const opt = document.createElement("option"); opt.value = c.id; opt.textContent = c.name; sel.appendChild(opt); });
    document.getElementById("pwd-conn-select-container").classList.remove("hidden");
    document.getElementById("pwd-password").value = "";
    document.getElementById("modalPasswordText").innerText = type === 'SUITE' ? `Ejecutar Suite #${targetId}` : `Ejecutar Caso #${targetId}`;
    getModalPwdInst().show();
}

export async function procesarPasswordSubmit(e) {
    e.preventDefault();
    const pwd = document.getElementById("pwd-password").value;
    const btn = document.getElementById("pwd-submit-btn");
    const spinner = document.getElementById("pwd-submit-spinner");
    const text = document.getElementById("pwd-submit-text");
    const connId = document.getElementById("pwd-connection-id").value;

    btn.disabled = true; spinner.classList.remove("hidden"); text.innerText = "Ejecutando...";

    try {
        if (execAction !== "TEST_CONN") {
            const conn = estado.conexiones.find(c => c.id == connId);
            if (conn) {
                if (conn.environment_type === 'STAGING') {
                    if (!window.confirm("ATENCIÓN: Está ejecutando en STAGING. ¿Está seguro de proceder? Las sentencias DML requerirán confirmación.")) {
                        btn.disabled = false; spinner.classList.add("hidden"); text.innerText = "Proceder";
                        return;
                    }
                } else if (conn.environment_type === 'PRODUCTION') {
                    if (!window.confirm("¡PELIGRO! Está ejecutando en PRODUCTION. Todo intento de DML será estrictamente rechazado por el backend. ¿Desea proceder con la ejecución de solo lectura?")) {
                        btn.disabled = false; spinner.classList.add("hidden"); text.innerText = "Proceder";
                        return;
                    }
                }
            }
        }

        if (execAction === "TEST_CONN") {
            await fetchAPI(`/connections/${execTargetId}/test`, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({password: pwd}) });
            getModalPwdInst().hide();
            Swal.fire("Éxito", "Conexión a base de datos exitosa.", "success");
        } else if (execAction === "CASE") {
            const res = await fetchAPI(`/execute/test-case/${execTargetId}`, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({connection_profile_id: parseInt(connId), password: pwd}) });
            getModalPwdInst().hide();
            let cl = res.status === 'PASS' ? 'success' : (res.status === 'FAIL' ? 'warning' : 'error');
            Swal.fire({
                title: `Resultado: ${res.status}`,
                html: `<b>Esperado:</b> ${escapeHTML(res.expected_result)}<br><b>Obtenido:</b> ${escapeHTML(res.actual_result)}<br><small class="text-muted">Duración: ${res.duration_ms}ms</small>`,
                icon: cl
            });
            actualizarDatosProyectoActivo();
        } else if (execAction === "SUITE") {
            const res = await fetchAPI(`/execute/suite/${execTargetId}`, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({connection_profile_id: parseInt(connId), password: pwd}) });
            getModalPwdInst().hide();
            const isPass = res.failed === 0 && res.errors === 0;
            let detHtml = '<hr><div class="text-start" style="max-height:200px; overflow-y:auto; font-size:0.85em;">';
            res.details.forEach(r => {
                let col = r.status === 'PASS' ? 'text-success' : (r.status === 'FAIL' ? 'text-warning' : 'text-danger');
                detHtml += `<div class="${col}">[${r.status}] Caso #${r.test_case_id} (${r.duration_ms}ms)</div>`;
            });
            detHtml += '</div>';
            Swal.fire({
                title: isPass ? 'Suite Exitosa' : 'Suite con Fallos',
                html: `<div class="text-start"><div><b>Total:</b> ${res.total_tests}</div>
                    <div class="text-success"><b>PASS:</b> ${res.passed}</div>
                    <div class="text-warning"><b>FAIL:</b> ${res.failed}</div>
                    <div class="text-danger"><b>ERROR:</b> ${res.errors}</div>
                    <div class="text-muted small">Duración total: ${res.total_duration_ms}ms</div></div>${detHtml}`,
                icon: isPass ? 'success' : 'warning'
            });
            actualizarDatosProyectoActivo();
        }
    } catch(err) {
        getModalPwdInst().hide();
        handleAPIError(err);
    } finally {
        document.getElementById("pwd-password").value = "";
        btn.disabled = false; spinner.classList.add("hidden"); text.innerText = "Proceder";
    }
}
