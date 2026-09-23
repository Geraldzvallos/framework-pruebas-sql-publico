import { estado } from '../core/estado.js';
import { fetchAPI, handleAPIError } from '../../app.js';
import { escapeHTML } from '../core/utilidades.js';

export async function cargarHistorial() {
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
