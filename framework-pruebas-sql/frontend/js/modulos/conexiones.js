import { estado } from '../core/estado.js';
import { fetchAPI, handleAPIError } from '../../app.js';
import { escapeHTML, abrirModalGeneral, modalGeneralAction, modalGeneralId } from '../core/utilidades.js';

let abrirTestConexionFn = null;

export function initConexiones(testConexionFn) {
    abrirTestConexionFn = testConexionFn;
}

export function formConexion(c = null) {
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

export async function saveConexion() {
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

export async function cargarConexiones() {
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
        tbody.querySelectorAll('.btn-test').forEach(b => b.addEventListener('click', () => {
            if (abrirTestConexionFn) abrirTestConexionFn(b.dataset.id);
        }));
        tbody.querySelectorAll('.btn-edit').forEach(b => b.addEventListener('click', () => formConexion(estado.conexiones.find(x => x.id == b.dataset.id))));
        tbody.querySelectorAll('.btn-del').forEach(b => b.addEventListener('click', () => eliminarConexion(b.dataset.id)));
    } catch(e) { handleAPIError(e); }
}

export async function eliminarConexion(id) {
    const res = await Swal.fire({ title: '¿Eliminar perfil?', icon: 'warning', showCancelButton: true, confirmButtonText: 'Eliminar' });
    if (res.isConfirmed) {
        try { await fetchAPI(`/connections/${id}`, { method: 'DELETE' }); cargarConexiones(); } catch(e) { handleAPIError(e); }
    }
}
