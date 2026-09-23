import { estado } from '../core/estado.js';
import { fetchAPI, handleAPIError } from '../../app.js';
import { escapeHTML, abrirModalGeneral, modalGeneralAction, modalGeneralId } from '../core/utilidades.js';

let updateGlobalProjectsFn = null;

export function initProyectos(updateFn) {
    updateGlobalProjectsFn = updateFn;
}

export function formProyecto(p = null) {
    const html = `
        <div class="mb-3"><label class="form-label">Nombre</label><input type="text" id="f-proj-name" class="form-control" required value="${escapeHTML(p?.name||'')}"></div>
        <div class="mb-3"><label class="form-label">Descripción</label><textarea id="f-proj-desc" class="form-control">${escapeHTML(p?.description||'')}</textarea></div>
    `;
    abrirModalGeneral(p ? "Editar Proyecto" : "Nuevo Proyecto", html, p ? "PROJ_EDIT" : "PROJ_NEW", p?.id);
}

export async function saveProyecto() {
    const payload = { name: document.getElementById("f-proj-name").value, description: document.getElementById("f-proj-desc").value };
    if (modalGeneralAction === "PROJ_NEW") {
        await fetchAPI("/projects/", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
        Swal.fire("Éxito", "Proyecto creado.", "success");
    } else {
        await fetchAPI(`/projects/${modalGeneralId}`, { method: "PUT", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
        Swal.fire("Éxito", "Proyecto actualizado.", "success");
    }
    if (updateGlobalProjectsFn) await updateGlobalProjectsFn();
    if (!document.getElementById("section-proyectos").classList.contains("hidden")) cargarProyectos();
}

export function cargarProyectos() {
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

export async function eliminarProyecto(id) {
    const res = await Swal.fire({ title: '¿Eliminar proyecto?', icon: 'warning', showCancelButton: true, confirmButtonText: 'Eliminar' });
    if (res.isConfirmed) {
        try {
            await fetchAPI(`/projects/${id}`, { method: 'DELETE' });
            Swal.fire("Eliminado", "", "success");
            if (updateGlobalProjectsFn) await updateGlobalProjectsFn();
            cargarProyectos();
        } catch(e) { handleAPIError(e); }
    }
}
