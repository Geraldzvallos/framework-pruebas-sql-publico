import { estado } from '../core/estado.js';
import { fetchAPI, handleAPIError } from '../../app.js';
import { escapeHTML, abrirModalGeneral, modalGeneralAction, modalGeneralId } from '../core/utilidades.js';

let abrirEjecucionFn = null;

export function initSuites(ejecucionFn) {
    abrirEjecucionFn = ejecucionFn;
}

export function formSuite(s = null) {
    const html = `
        <div class="mb-3"><label class="form-label">Nombre</label><input type="text" id="f-suite-name" class="form-control" required value="${escapeHTML(s?.name||'')}"></div>
        <div class="mb-3"><label class="form-label">Descripción</label><textarea id="f-suite-desc" class="form-control">${escapeHTML(s?.description||'')}</textarea></div>
    `;
    abrirModalGeneral(s ? "Editar Suite" : "Nueva Suite", html, s ? "SUITE_EDIT" : "SUITE_NEW", s?.id);
}

export async function saveSuite() {
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

export async function cargarSuites() {
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
        cont.querySelectorAll('.btn-exec').forEach(b => b.addEventListener('click', () => {
            if (abrirEjecucionFn) abrirEjecucionFn('SUITE', b.dataset.id);
        }));
    } catch(e) { handleAPIError(e); }
}
