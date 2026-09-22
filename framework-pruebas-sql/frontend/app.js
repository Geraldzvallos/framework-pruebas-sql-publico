const API_URL = window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1") ? "/api" : window.location.origin + "/api";

let estado = {
    proyectoActivoId: null,
    proyectos: [],
    conexiones: [],
    casos: [],
    suites: [],
    histSkip: 0,
    histLimit: 20
};

function escapeHTML(str) {
    if (str === null || str === undefined) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function handleAPIError(e) {
    let msg = "Error en la petición.";
    if (typeof e.message === 'string') msg = escapeHTML(e.message);
    else if (Array.isArray(e.message)) {
        msg = "<ul class='text-start'>" + e.message.map(err => `<li><b>${escapeHTML(err.loc?.[err.loc.length-1] || 'Campo')}</b>: ${escapeHTML(err.msg)}</li>`).join('') + "</ul>";
    } else if (typeof e.message === 'object') {
        msg = escapeHTML(JSON.stringify(e.message));
    }
    Swal.fire({ title: "Error " + (e.status || ""), html: msg, icon: "error" });
}

async function fetchAPI(endpoint, options = {}) {
    const res = await fetch(API_URL + endpoint, options);
    if (!res.ok) {
        let errorMsg = 'Error en el servidor';
        try { const errorData = await res.json(); errorMsg = errorData.detail || errorMsg; } catch (e) {}
        throw { status: res.status, message: errorMsg };
    }
    if (res.status === 204) return null;
    return await res.json();
}

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
        // preserve the header if it exists
        const header = c.querySelector('h5');
        c.innerHTML = (header ? header.outerHTML : '') + linksHtml;
    });

    document.querySelectorAll(".nav-link-custom").forEach(link => {
        link.addEventListener("click", (e) => {
            const section = e.target.closest('a').getAttribute("data-section");
            mostrarSeccion(section);
            // close offcanvas if on mobile
            const offcanvasEl = document.getElementById('offcanvasMenu');
            if (offcanvasEl) {
                const offcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl);
                if (offcanvas) offcanvas.hide();
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", async () => {
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
        cargarCasos().then(() => cargarSuites()); // ensure cases are loaded first
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
        // La API admite como máximo 100 registros por petición.
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

let modalGeneralAction = null;
let modalGeneralId = null;
const modalGeneralInst = new bootstrap.Modal(document.getElementById("modalGeneral"));

function abrirModalGeneral(title, html, actionType, id = null) {
    document.getElementById("modalGeneralTitle").innerText = title;
    document.getElementById("modalGeneralBody").innerHTML = html;
    modalGeneralAction = actionType;
    modalGeneralId = id;
    document.getElementById("modalGeneralSubmit").disabled = false;
    modalGeneralInst.show();
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
        modalGeneralInst.hide();
    } catch (err) {
        handleAPIError(err);
    } finally {
        btn.disabled = false;
    }
}

// === PROYECTOS ===
function formProyecto(p = null) {
    const html = `
        <div class="mb-3"><label class="form-label">Nombre</label><input type="text" id="f-proj-name" class="form-control" required value="${escapeHTML(p?.name||'')}"></div>
        <div class="mb-3"><label class="form-label">Descripción</label><textarea id="f-proj-desc" class="form-control">${escapeHTML(p?.description||'')}</textarea></div>
    `;
    abrirModalGeneral(p ? "Editar Proyecto" : "Nuevo Proyecto", html, p ? "PROJ_EDIT" : "PROJ_NEW", p?.id);
}

async function saveProyecto() {
    const payload = { name: document.getElementById("f-proj-name").value, description: document.getElementById("f-proj-desc").value };
    if (modalGeneralAction === "PROJ_NEW") {
        await fetchAPI("/projects/", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
        Swal.fire("Éxito", "Proyecto creado.", "success");
    } else {
        await fetchAPI(`/projects/${modalGeneralId}`, { method: "PUT", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
        Swal.fire("Éxito", "Proyecto actualizado.", "success");
    }
    await cargarProyectosGlobal();
    if (!document.getElementById("section-proyectos").classList.contains("hidden")) cargarProyectos();
}

function cargarProyectos() {
    const tbody = document.getElementById("tabla-proyectos");
    tbody.innerHTML = "";
    estado.proyectos.forEach(p => {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${p.id}</td><td><strong>${escapeHTML(p.name)}</strong></td><td>${escapeHTML(p.description)}</td>
            <td class="text-end pe-4">
                <button class="btn btn-sm btn-outline-secondary btn-edit" data-id="${p.id}"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-danger btn-del" data-id="${p.id}"><i class="bi bi-trash"></i></button>
            </td>`;
        tbody.appendChild(tr);
    });
    tbody.querySelectorAll('.btn-edit').forEach(b => b.addEventListener('click', () => formProyecto(estado.proyectos.find(x => x.id == b.dataset.id))));
    tbody.querySelectorAll('.btn-del').forEach(b => b.addEventListener('click', () => eliminarProyecto(b.dataset.id)));
}

async function eliminarProyecto(id) {
    const res = await Swal.fire({ title: '¿Eliminar proyecto?', icon: 'warning', showCancelButton: true, confirmButtonText: 'Eliminar' });
    if (res.isConfirmed) {
        try {
            await fetchAPI(`/projects/${id}`, { method: 'DELETE' });
            Swal.fire("Eliminado", "", "success");
            await cargarProyectosGlobal();
            cargarProyectos();
        } catch(e) { handleAPIError(e); }
    }
}

// === CONEXIONES ===
function formConexion(c = null) {
    const html = `
        <div class="row">
            <div class="col-md-6 mb-3"><label class="form-label">Nombre del Perfil</label><input type="text" id="f-conn-name" class="form-control" required value="${escapeHTML(c?.name||'')}"></div>
            <div class="col-md-6 mb-3"><label class="form-label">Host</label><input type="text" id="f-conn-host" class="form-control" required value="${escapeHTML(c?.host||'')}"></div>
            <div class="col-md-4 mb-3"><label class="form-label">Puerto</label><input type="number" id="f-conn-port" class="form-control" required value="${c?.port||1521}"></div>
            <div class="col-md-8 mb-3"><label class="form-label">Service Name</label><input type="text" id="f-conn-service" class="form-control" required value="${escapeHTML(c?.service_name||'')}"></div>
            <div class="col-md-12 mb-3"><label class="form-label">Usuario</label><input type="text" id="f-conn-user" class="form-control" required value="${escapeHTML(c?.username||'')}"></div>
        </div>
        <small class="text-muted">Motor: ORACLE. Las contraseñas no se persisten.</small>
    `;
    abrirModalGeneral(c ? "Editar Perfil" : "Nuevo Perfil", html, c ? "CONN_EDIT" : "CONN_NEW", c?.id);
}

async function saveConexion() {
    const payload = {
        project_id: estado.proyectoActivoId,
        name: document.getElementById("f-conn-name").value,
        engine: "oracle",
        host: document.getElementById("f-conn-host").value,
        port: parseInt(document.getElementById("f-conn-port").value),
        service_name: document.getElementById("f-conn-service").value,
        username: document.getElementById("f-conn-user").value
    };
    if (modalGeneralAction === "CONN_NEW") {
        await fetchAPI("/connections/", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
        Swal.fire("Éxito", "Perfil creado.", "success");
    } else {
        await fetchAPI(`/connections/${modalGeneralId}`, { method: "PUT", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
        Swal.fire("Éxito", "Perfil actualizado.", "success");
    }
    cargarConexiones();
}

async function cargarConexiones() {
    try {
        estado.conexiones = await fetchAPI(`/connections/?project_id=${estado.proyectoActivoId}`);
        const tbody = document.getElementById("tabla-conexiones");
        tbody.innerHTML = "";
        estado.conexiones.forEach(c => {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${c.id}</td><td><strong>${escapeHTML(c.name)}</strong></td><td>${escapeHTML(c.host)}:${c.port}</td>
                <td>${escapeHTML(c.service_name)}</td><td>${escapeHTML(c.username)}</td>
                <td class="text-end pe-4">
                    <button class="btn btn-sm btn-outline-info btn-test" data-id="${c.id}"><i class="bi bi-plug"></i></button>
                    <button class="btn btn-sm btn-outline-secondary btn-edit" data-id="${c.id}"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-outline-danger btn-del" data-id="${c.id}"><i class="bi bi-trash"></i></button>
                </td>`;
            tbody.appendChild(tr);
        });
        tbody.querySelectorAll('.btn-test').forEach(b => b.addEventListener('click', () => abrirTestConexion(b.dataset.id)));
        tbody.querySelectorAll('.btn-edit').forEach(b => b.addEventListener('click', () => formConexion(estado.conexiones.find(x => x.id == b.dataset.id))));
        tbody.querySelectorAll('.btn-del').forEach(b => b.addEventListener('click', () => eliminarConexion(b.dataset.id)));
    } catch(e) { handleAPIError(e); }
}

async function eliminarConexion(id) {
    const res = await Swal.fire({ title: '¿Eliminar perfil?', icon: 'warning', showCancelButton: true, confirmButtonText: 'Eliminar' });
    if (res.isConfirmed) {
        try { await fetchAPI(`/connections/${id}`, { method: 'DELETE' }); cargarConexiones(); } catch(e) { handleAPIError(e); }
    }
}

// === CASOS DE PRUEBA ===
function formCaso(c = null) {
    const html = `
        <div class="mb-3"><label class="form-label">Nombre</label><input type="text" id="f-caso-name" class="form-control" required value="${escapeHTML(c?.name||'')}"></div>
        <div class="mb-3"><label class="form-label">Descripción</label><textarea id="f-caso-desc" class="form-control">${escapeHTML(c?.description||'')}</textarea></div>
        <div class="mb-3"><label class="form-label">Sentencia SQL</label><textarea class="form-control font-monospace text-primary" id="f-caso-sql" rows="3" required>${escapeHTML(c?.sql_query||'')}</textarea></div>
        <div class="row">
            <div class="col-md-6 mb-3"><label class="form-label">Tipo Validación</label>
                <select class="form-select" id="f-caso-val" required onchange="actualizarPlaceholderCaso()">
                    <option value="ROW_COUNT" ${c?.validation_type==='ROW_COUNT'?'selected':''}>ROW_COUNT</option>
                    <option value="EXISTS" ${c?.validation_type==='EXISTS'?'selected':''}>EXISTS</option>
                </select>
            </div>
            <div class="col-md-6 mb-3"><label class="form-label">Resultado Esperado</label><input type="text" id="f-caso-exp" class="form-control" required value="${escapeHTML(c?.expected_result||'')}"></div>
        </div>
    `;
    abrirModalGeneral(c ? "Editar Caso" : "Nuevo Caso", html, c ? "CASE_EDIT" : "CASE_NEW", c?.id);
    window.actualizarPlaceholderCaso = function() {
        const v = document.getElementById("f-caso-val").value;
        document.getElementById("f-caso-exp").placeholder = v === 'EXISTS' ? 'true o false' : 'Ej: 1';
    };
    window.actualizarPlaceholderCaso();
}

async function saveCaso() {
    let exp = document.getElementById("f-caso-exp").value.trim();
    const v = document.getElementById("f-caso-val").value;
    if (v === 'EXISTS') {
        exp = exp.toLowerCase();
        if (exp !== 'true' && exp !== 'false') throw {status: 422, message: "Para EXISTS el valor esperado debe ser 'true' o 'false'."};
    }
    if (v === 'ROW_COUNT' && !/^\d+$/.test(exp)) throw {status: 422, message: "Para ROW_COUNT debe ser un entero >= 0."};
    
    const payload = { project_id: estado.proyectoActivoId, name: document.getElementById("f-caso-name").value, description: document.getElementById("f-caso-desc").value, sql_query: document.getElementById("f-caso-sql").value, validation_type: v, expected_result: exp };
    
    if (modalGeneralAction === "CASE_NEW") {
        await fetchAPI("/test-cases/", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
        Swal.fire("Éxito", "Caso creado.", "success");
    } else {
        await fetchAPI(`/test-cases/${modalGeneralId}`, { method: "PUT", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
        Swal.fire("Éxito", "Caso actualizado.", "success");
    }
    cargarCasos();
}

async function cargarCasos() {
    try {
        estado.casos = await fetchAPI(`/test-cases/?project_id=${estado.proyectoActivoId}`);
        const tbody = document.getElementById("tabla-casos");
        tbody.innerHTML = "";
        estado.casos.forEach(c => {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${c.id}</td><td><strong>${escapeHTML(c.name)}</strong></td>
                <td class="text-truncate-custom font-monospace text-primary small sql-cell" data-sql="${escapeHTML(c.sql_query)}">${escapeHTML(c.sql_query)}</td>
                <td><span class="badge bg-secondary">${c.validation_type}</span></td><td>${escapeHTML(c.expected_result)}</td>
                <td class="text-end pe-4">
                    <button class="btn btn-sm btn-outline-success btn-exec" data-id="${c.id}"><i class="bi bi-play-fill"></i></button>
                    <button class="btn btn-sm btn-outline-secondary btn-edit" data-id="${c.id}"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-outline-danger btn-del" data-id="${c.id}"><i class="bi bi-trash"></i></button>
                </td>`;
            tbody.appendChild(tr);
        });
        tbody.querySelectorAll('.sql-cell').forEach(c => c.addEventListener('click', (e) => {
            Swal.fire({title: "SQL Completo", html: `<pre class="text-start bg-light p-3 border rounded"><code>${e.target.getAttribute('data-sql')}</code></pre>`, width: '800px'});
        }));
        tbody.querySelectorAll('.btn-exec').forEach(b => b.addEventListener('click', () => abrirEjecucion('CASE', b.dataset.id)));
        tbody.querySelectorAll('.btn-edit').forEach(b => b.addEventListener('click', () => formCaso(estado.casos.find(x => x.id == b.dataset.id))));
        tbody.querySelectorAll('.btn-del').forEach(b => b.addEventListener('click', () => eliminarCaso(b.dataset.id)));
    } catch(e) { handleAPIError(e); }
}

async function eliminarCaso(id) {
    const res = await Swal.fire({ title: '¿Eliminar caso?', icon: 'warning', showCancelButton: true, confirmButtonText: 'Eliminar' });
    if (res.isConfirmed) {
        try { await fetchAPI(`/test-cases/${id}`, { method: 'DELETE' }); cargarCasos(); } catch(e) { handleAPIError(e); }
    }
}

// === SUITES ===
function formSuite(s = null) {
    const html = `
        <div class="mb-3"><label class="form-label">Nombre</label><input type="text" id="f-suite-name" class="form-control" required value="${escapeHTML(s?.name||'')}"></div>
        <div class="mb-3"><label class="form-label">Descripción</label><textarea id="f-suite-desc" class="form-control">${escapeHTML(s?.description||'')}</textarea></div>
    `;
    abrirModalGeneral(s ? "Editar Suite" : "Nueva Suite", html, s ? "SUITE_EDIT" : "SUITE_NEW", s?.id);
}

async function saveSuite() {
    const payload = { project_id: estado.proyectoActivoId, name: document.getElementById("f-suite-name").value, description: document.getElementById("f-suite-desc").value };
    if (modalGeneralAction === "SUITE_NEW") {
        await fetchAPI("/suites/", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
        Swal.fire("Éxito", "Suite creada.", "success");
    } else {
        await fetchAPI(`/suites/${modalGeneralId}`, { method: "PUT", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
        Swal.fire("Éxito", "Suite actualizada.", "success");
    }
    cargarSuites();
}

async function cargarSuites() {
    try {
        estado.suites = await fetchAPI(`/suites/?project_id=${estado.proyectoActivoId}`);
        const cont = document.getElementById("contenedor-suites");
        cont.innerHTML = "";
        if (estado.suites.length === 0) { cont.innerHTML = "<div class='text-muted text-center'>No hay suites.</div>"; return; }
        
        estado.suites.forEach(s => {
            const arr = s.test_cases || [];
            let casesHtml = arr.map(c => `<div class="d-flex justify-content-between text-muted small border-bottom py-1">
                <span>${escapeHTML(c.name)}</span>
                <button class="btn btn-sm text-danger p-0 m-0 btn-retirar-caso" data-suite="${s.id}" data-case="${c.id}"><i class="bi bi-x-circle"></i></button></div>`).join("");
            
            const col = document.createElement("div"); col.className = "col-md-6 mb-4";
            col.innerHTML = `
                <div class="card border-primary h-100">
                    <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                        <span>${escapeHTML(s.name)}</span>
                        <div><span class="badge bg-light text-primary me-2">${arr.length}</span>
                        <button class="btn btn-sm btn-outline-light border-0 btn-edit" data-id="${s.id}"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-outline-light border-0 btn-del" data-id="${s.id}"><i class="bi bi-trash"></i></button></div>
                    </div>
                    <div class="card-body">
                        <p class="small text-muted">${escapeHTML(s.description)}</p>
                        <div class="mb-3">${casesHtml || '<span class="text-muted small">Sin casos</span>'}</div>
                        <div class="d-flex gap-2">
                            <select class="form-select form-select-sm sel-asoc" data-suite="${s.id}"><option value="">Añadir caso...</option></select>
                            <button class="btn btn-sm btn-outline-secondary btn-asoc" data-suite="${s.id}">Asociar</button>
                        </div>
                    </div>
                    <div class="card-footer text-end bg-transparent"><button class="btn btn-primary btn-sm btn-exec" data-id="${s.id}"><i class="bi bi-play-fill"></i> Ejecutar</button></div>
                </div>`;
            cont.appendChild(col);
            
            const sel = col.querySelector('.sel-asoc');
            estado.casos.forEach(c => {
                if (!arr.some(xc => xc.id === c.id)) {
                    const opt = document.createElement("option"); opt.value = c.id; opt.textContent = `[#${c.id}] ${c.name}`; sel.appendChild(opt);
                }
            });
        });
        
        cont.querySelectorAll('.btn-retirar-caso').forEach(b => b.addEventListener('click', async (e) => {
            const btn = e.target.closest('button');
            try { await fetchAPI(`/suites/${btn.dataset.suite}/test-cases/${btn.dataset.case}`, { method: 'DELETE' }); cargarSuites(); } catch(err) { handleAPIError(err); }
        }));
        cont.querySelectorAll('.btn-asoc').forEach(b => b.addEventListener('click', async (e) => {
            const suiteId = e.target.dataset.suite;
            const caseId = cont.querySelector(`.sel-asoc[data-suite="${suiteId}"]`).value;
            if (!caseId) return;
            try { await fetchAPI(`/suites/${suiteId}/test-cases/${caseId}`, { method: 'POST' }); cargarSuites(); } catch(err) { handleAPIError(err); }
        }));
        cont.querySelectorAll('.btn-edit').forEach(b => b.addEventListener('click', () => formSuite(estado.suites.find(x => x.id == b.dataset.id))));
        cont.querySelectorAll('.btn-del').forEach(b => b.addEventListener('click', async (e) => {
            const id = e.target.closest('button').dataset.id;
            const res = await Swal.fire({ title: '¿Eliminar suite?', icon: 'warning', showCancelButton: true });
            if (res.isConfirmed) { try { await fetchAPI(`/suites/${id}`, { method: 'DELETE' }); cargarSuites(); } catch(err) { handleAPIError(err); } }
        }));
        cont.querySelectorAll('.btn-exec').forEach(b => b.addEventListener('click', () => abrirEjecucion('SUITE', b.dataset.id)));
    } catch(e) { handleAPIError(e); }
}

// === CONTRASEÑA Y EJECUCIÓN ===
const modalPwdInst = new bootstrap.Modal(document.getElementById("modalPassword"));
let execAction = null;
let execTargetId = null;

function abrirTestConexion(connId) {
    execAction = "TEST_CONN"; execTargetId = connId;
    document.getElementById("pwd-conn-select-container").classList.add("hidden");
    document.getElementById("pwd-password").value = "";
    document.getElementById("modalPasswordText").innerText = "Probar perfil de conexión #" + connId;
    modalPwdInst.show();
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
    modalPwdInst.show();
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
            modalPwdInst.hide();
            Swal.fire("Éxito", "Conexión a base de datos exitosa.", "success");
        } else if (execAction === "CASE") {
            const res = await fetchAPI(`/execute/test-case/${execTargetId}`, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({connection_profile_id: parseInt(connId), password: pwd}) });
            modalPwdInst.hide();
            let cl = res.status === 'PASS' ? 'success' : (res.status === 'FAIL' ? 'warning' : 'error');
            Swal.fire({
                title: `Resultado: ${res.status}`,
                html: `<b>Esperado:</b> ${escapeHTML(res.expected_result)}<br><b>Obtenido:</b> ${escapeHTML(res.actual_result)}<br><small class="text-muted">Duración: ${res.duration_ms}ms</small>`,
                icon: cl
            });
            actualizarDatosProyectoActivo();
        } else if (execAction === "SUITE") {
            const res = await fetchAPI(`/execute/suite/${execTargetId}`, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({connection_profile_id: parseInt(connId), password: pwd}) });
            modalPwdInst.hide();
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
        modalPwdInst.hide();
        handleAPIError(err);
    } finally {
        document.getElementById("pwd-password").value = ""; // Limpiar siempre
        btn.disabled = false; spinner.classList.add("hidden"); text.innerText = "Proceder";
    }
}

// === HISTORIAL ===
async function cargarHistorial() {
    const status = document.getElementById("filtro-hist-status").value;
    const suiteId = document.getElementById("filtro-hist-suite").value;
    const caseId = document.getElementById("filtro-hist-case").value;
    
    let url = `/history/?skip=${estado.histSkip}&limit=${estado.histLimit}`;
    if (estado.proyectoActivoId) url += `&project_id=${estado.proyectoActivoId}`;
    if (status) url += `&status=${status}`;
    if (suiteId) url += `&suite_id=${suiteId}`;
    if (caseId) url += `&test_case_id=${caseId}`;
    
    try {
        const hist = await fetchAPI(url);
        const tbody = document.getElementById("tabla-historial");
        tbody.innerHTML = "";
        
        document.getElementById("btn-hist-prev").disabled = estado.histSkip === 0;
        document.getElementById("btn-hist-next").disabled = hist.length < estado.histLimit;
        document.getElementById("historial-pag-info").innerText = `Registros ${estado.histSkip} - ${estado.histSkip + hist.length}`;
        
        if (hist.length === 0) { tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No hay registros</td></tr>'; return; }
        
        hist.forEach(h => {
            const badgeColor = h.status === 'PASS' ? 'bg-success' : (h.status === 'FAIL' ? 'bg-warning text-dark' : 'bg-danger');
            const isSuite = h.suite_id !== null;
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${h.id}</td><td>${isSuite ? 'Suite' : 'Individual'}</td>
                <td><small class="text-muted">C-${h.test_case_id}${isSuite?' / S-'+h.suite_id:''}</small></td>
                <td><span class="badge ${badgeColor}">${h.status}</span></td>
                <td>${h.duration_ms}</td>
                <td>${h.rollback_applied ? '<i class="bi bi-check-circle text-success"></i>' : '-'}</td>
                <td class="text-end pe-4"><button class="btn btn-sm btn-outline-secondary btn-det" data-json="${escapeHTML(JSON.stringify(h))}"><i class="bi bi-eye"></i></button></td>`;
            tbody.appendChild(tr);
        });
        
        tbody.querySelectorAll('.btn-det').forEach(b => b.addEventListener('click', (e) => {
            const h = JSON.parse(e.target.closest('button').dataset.json);
            const rMsg = h.rollback_error ? `<br><span class="text-danger">Error de Rollback: ${escapeHTML(h.rollback_error)}</span>` : '';
            const eMsg = h.error_message ? `<br><span class="text-danger">Error: ${escapeHTML(h.error_message)}</span>` : '';
            Swal.fire({
                title: `Ejecución #${h.id}`,
                html: `<div class="text-start">
                    <b>Esperado:</b> ${escapeHTML(h.expected_result)}<br><b>Obtenido:</b> ${escapeHTML(h.actual_result)}
                    <br><b>Rollback:</b> ${h.rollback_applied ? 'Sí' : 'No'}
                    ${rMsg}${eMsg}</div>`,
                icon: h.status === 'PASS' ? 'success' : (h.status === 'FAIL' ? 'warning' : 'error')
            });
        }));
    } catch(e) { handleAPIError(e); }
}
