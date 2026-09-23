// API functions required by tests to be in app.js
export const API_URL = window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1") ? "/api" : window.location.origin + "/api";

export function handleAPIError(e) {
    let msg = "Error en la petición.";
    if (typeof e.message === 'string') msg = escapeHTML(e.message);
    else if (Array.isArray(e.message)) {
        msg = "<ul class='text-start'>" + e.message.map(err => `<li><b>${escapeHTML(err.loc?.[err.loc.length-1] || 'Campo')}</b>: ${escapeHTML(err.msg)}</li>`).join('') + "</ul>";
    } else if (typeof e.message === 'object') {
        msg = escapeHTML(JSON.stringify(e.message));
    }
    Swal.fire({ title: "Error " + (e.status || ""), html: msg, icon: "error" });
}

export async function fetchAPI(endpoint, options = {}) {
    const res = await fetch(API_URL + endpoint, options);
    if (!res.ok) {
        let errorMsg = 'Error en el servidor';
        try { const errorData = await res.json(); errorMsg = errorData.detail || errorMsg; } catch (e) {}
        throw { status: res.status, message: errorMsg };
    }
    if (res.status === 204) return null;
    return await res.json();
}
import { estado } from './js/core/estado.js';
import { escapeHTML, modalGeneralAction, hideModalGeneral } from './js/core/utilidades.js';

import { initProyectos, cargarProyectos, formProyecto, saveProyecto } from './js/modulos/proyectos.js';
import { initConexiones, cargarConexiones, formConexion, saveConexion } from './js/modulos/conexiones.js';
import { initCasos, cargarCasos, formCaso, saveCaso } from './js/modulos/casos.js';
import { initSuites, cargarSuites, formSuite, saveSuite } from './js/modulos/suites.js';
import { cargarHistorial } from './js/modulos/historial.js';

// Setup routing
function setupSidebarLinks() {
    const linksHtml = `
        <a class="nav-link-custom active" data-section="dashboard"><i class="bi bi-speedometer2 me-2"></i> Dashboard</a>
        <a class="nav-link-custom" data-section="proyectos"><i class="bi bi-folder me-2"></i> Proyectos</a>
        <a class="nav-link-custom" data-section="conexiones"><i class="bi bi-hdd-network me-2"></i> Conexiones Oracle</a>
        <a class="nav-link-custom" data-section="casos"><i class="bi bi-code-square me-2"></i> Casos de Prueba</a>
        <a class="nav-link-custom" data-section="suites"><i class="bi bi-collection me-2"></i> Suites</a>
        <a class="nav-link-custom" data-section="historial"><i class="bi bi-clock-history me-2"></i> Historial</a>
        <a class="nav-link-custom" data-section="ayuda"><i class="bi bi-question-circle me-2"></i> Ayuda</a>
    `;
    document.querySelectorAll(".sidebar-links-container").forEach(c => {
        const header = c.querySelector('h5');
        c.innerHTML = (header ? header.outerHTML : '') + linksHtml;
    });

    document.querySelectorAll(".nav-link-custom").forEach(link => {
        link.addEventListener("click", (e) => {
            const section = e.target.closest('a').getAttribute("data-section");
            mostrarSeccion(section);
            const offcanvasEl = document.getElementById('offcanvasMenu');
            if (offcanvasEl) {
                const offcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl);
                if (offcanvas) offcanvas.hide();
            }
        });
    });
}

function mostrarSeccion(section) {
    document.querySelectorAll(".section-container").forEach(el => el.classList.add("hidden"));
    document.querySelectorAll(".nav-link-custom").forEach(el => el.classList.remove("active"));
    document.querySelectorAll(`.nav-link-custom[data-section="${section}"]`).forEach(el => el.classList.add("active"));
    
    const titleMap = {
        'dashboard': 'Dashboard', 'proyectos': 'Gestión de Proyectos', 'conexiones': 'Conexiones Oracle',
        'casos': 'Casos de Prueba', 'suites': 'Suites de Pruebas', 'historial': 'Historial de Ejecuciones', 'ayuda': 'Guía de Uso'
    };
    document.getElementById("titulo-seccion").innerText = titleMap[section] || 'Dashboard';
    
    const requiresProject = ['conexiones', 'casos', 'suites', 'historial'];
    if (requiresProject.includes(section) && !estado.proyectoActivoId) {
        document.getElementById("global-alert").classList.remove("hidden");
        return;
    } else {
        document.getElementById("global-alert").classList.add("hidden");
        if (section !== 'dashboard') {
            document.getElementById(`section-${section}`).classList.remove("hidden");
        }
    }

    if (section === 'proyectos') cargarProyectos();
    else if (section === 'conexiones') cargarConexiones();
    else if (section === 'casos') cargarCasos();
    else if (section === 'suites') {
        cargarCasos().then(() => cargarSuites());
    }
    else if (section === 'historial') cargarHistorial();
}

async function cargarProyectosGlobal() {
    try {
        estado.proyectos = await fetchAPI("/projects/");
        document.getElementById("kpi-proyectos").innerText = estado.proyectos.length;
        
        const select = document.getElementById("select-proyecto-activo");
        const valActual = select.value;
        select.innerHTML = '<option value="">Seleccione un proyecto...</option>';
        estado.proyectos.forEach(p => {
            const opt = document.createElement("option");
            opt.value = p.id; opt.textContent = p.name;
            select.appendChild(opt);
        });
        
        if (valActual && estado.proyectos.some(p => p.id == valActual)) {
            select.value = valActual;
            estado.proyectoActivoId = parseInt(valActual);
        } else if (estado.proyectos.length > 0) {
            select.value = estado.proyectos[0].id;
            estado.proyectoActivoId = estado.proyectos[0].id;
        } else {
            estado.proyectoActivoId = null;
        }
        
        await actualizarDatosProyectoActivo();
    } catch (e) { console.error("Error al cargar proyectos globales", e); }
}

async function actualizarDatosProyectoActivo() {
    if (!estado.proyectoActivoId) {
        document.getElementById("kpi-pass").innerText = "0";
        document.getElementById("kpi-fail").innerText = "0";
        document.getElementById("kpi-error").innerText = "0";
        return;
    }
    const activeLink = document.querySelector(".nav-link-custom.active");
    const activeSection = activeLink ? activeLink.getAttribute("data-section") : "dashboard";
    try {
        const hist = await fetchAPI(`/history/?project_id=${estado.proyectoActivoId}&limit=100`);
        let p = 0, f = 0, er = 0;
        hist.forEach(h => { if(h.status==='PASS') p++; else if(h.status==='FAIL') f++; else er++; });
        document.getElementById("kpi-pass").innerText = p;
        document.getElementById("kpi-fail").innerText = f;
        document.getElementById("kpi-error").innerText = er;
        
    } catch (e) {
        document.getElementById("kpi-pass").innerText = "0";
        document.getElementById("kpi-fail").innerText = "0";
        document.getElementById("kpi-error").innerText = "0";
        handleAPIError(e);
    } finally {
        mostrarSeccion(activeSection);
    }
}

async function procesarModalGeneralSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById("modalGeneralSubmit");
    btn.disabled = true;
    try {
        if (modalGeneralAction.startsWith("PROJ")) await saveProyecto();
        else if (modalGeneralAction.startsWith("CONN")) await saveConexion();
        else if (modalGeneralAction.startsWith("CASE")) await saveCaso();
        else if (modalGeneralAction.startsWith("SUITE")) await saveSuite();
        hideModalGeneral();
    } catch (err) {
        handleAPIError(err);
    } finally {
        btn.disabled = false;
    }
}

// Execution and Connection Testing Modal logic
let modalPwdInst = null;
let execAction = null;
let execTargetId = null;

function getModalPwdInst() {
    if (!modalPwdInst) {
        modalPwdInst = new bootstrap.Modal(document.getElementById("modalPassword"));
    }
    return modalPwdInst;
}

function abrirTestConexion(connId) {
    execAction = "TEST_CONN"; execTargetId = connId;
    document.getElementById("pwd-conn-select-container").classList.add("hidden");
    document.getElementById("pwd-password").value = "";
    document.getElementById("modalPasswordText").innerText = "Probar perfil de conexión #" + connId;
    getModalPwdInst().show();
}

async function abrirEjecucion(type, targetId) {
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

async function procesarPasswordSubmit(e) {
    e.preventDefault();
    const pwd = document.getElementById("pwd-password").value;
    const btn = document.getElementById("pwd-submit-btn");
    const spinner = document.getElementById("pwd-submit-spinner");
    const text = document.getElementById("pwd-submit-text");
    const connId = document.getElementById("pwd-connection-id").value;
    
    btn.disabled = true; spinner.classList.remove("hidden"); text.innerText = "Ejecutando...";
    
    try {
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

// Initialization
document.addEventListener("DOMContentLoaded", async () => {
    // Inject dependencies into modules
    initProyectos(cargarProyectosGlobal);
    initConexiones(abrirTestConexion);
    initCasos(abrirEjecucion);
    initSuites(abrirEjecucion);

    setupSidebarLinks();

    try {
        await fetchAPI("/projects/");
        document.getElementById("api-status").className = "badge bg-success px-3 py-2";
        document.getElementById("api-status").innerText = "API: En línea";
    } catch (e) {
        document.getElementById("api-status").className = "badge bg-danger px-3 py-2";
        document.getElementById("api-status").innerText = "API: Desconectada";
    }

    document.getElementById("select-proyecto-activo").addEventListener("change", (e) => {
        estado.proyectoActivoId = e.target.value ? parseInt(e.target.value) : null;
        actualizarDatosProyectoActivo();
    });

    document.getElementById("btn-nuevo-proyecto").addEventListener("click", () => formProyecto());
    document.getElementById("btn-nuevo-perfil").addEventListener("click", () => formConexion());
    document.getElementById("btn-nuevo-caso").addEventListener("click", () => formCaso());
    document.getElementById("btn-nueva-suite").addEventListener("click", () => formSuite());
    document.getElementById("btn-filtrar-historial").addEventListener("click", () => { estado.histSkip = 0; cargarHistorial(); });
    document.getElementById("btn-hist-prev").addEventListener("click", () => { estado.histSkip = Math.max(0, estado.histSkip - estado.histLimit); cargarHistorial(); });
    document.getElementById("btn-hist-next").addEventListener("click", () => { estado.histSkip += estado.histLimit; cargarHistorial(); });
    document.getElementById("modalPasswordForm").addEventListener("submit", procesarPasswordSubmit);
    document.getElementById("modalGeneralForm").addEventListener("submit", procesarModalGeneralSubmit);

    await cargarProyectosGlobal();
    mostrarSeccion("dashboard");
});
