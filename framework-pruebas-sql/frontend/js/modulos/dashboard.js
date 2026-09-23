import { estado } from '../core/estado.js';
import { fetchAPI, handleAPIError } from '../core/api.js';
import { mostrarSeccion } from './navegacion.js';

export async function cargarProyectosGlobal() {
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

export async function actualizarDatosProyectoActivo() {
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
