import { estado } from '../core/estado.js';
import { cargarProyectos } from './proyectos.js';
import { cargarConexiones } from './conexiones.js';
import { cargarCasos } from './casos.js';
import { cargarSuites } from './suites.js';
import { cargarHistorial } from './historial.js';

export function setupSidebarLinks() {
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

export function mostrarSeccion(section) {
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
