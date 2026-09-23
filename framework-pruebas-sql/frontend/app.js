import { estado } from './js/core/estado.js';
import { fetchAPI } from './js/core/api.js';
import { hideModalGeneral, modalGeneralAction } from './js/core/utilidades.js';

import { initProyectos, formProyecto, saveProyecto } from './js/modulos/proyectos.js';
import { initConexiones, formConexion, saveConexion } from './js/modulos/conexiones.js';
import { initCasos, formCaso, saveCaso } from './js/modulos/casos.js';
import { initSuites, formSuite, saveSuite } from './js/modulos/suites.js';
import { cargarHistorial } from './js/modulos/historial.js';

import { setupSidebarLinks, mostrarSeccion } from './js/modulos/navegacion.js';
import { cargarProyectosGlobal, actualizarDatosProyectoActivo } from './js/modulos/dashboard.js';
import { abrirTestConexion, abrirEjecucion, procesarPasswordSubmit } from './js/modulos/ejecutor.js';

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
        // Errors are already handled by handleAPIError internally inside save* functions or here
        // If save* doesn't handle, we should. But actually save* doesn't catch them, so let's import handleAPIError
        const { handleAPIError } = await import('./js/core/api.js');
        handleAPIError(err);
    } finally {
        btn.disabled = false;
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
