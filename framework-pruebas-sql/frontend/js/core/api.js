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

function escapeHTML(str) {
    if (!str) return '';
    return str.toString().replace(/[&<>'"]/g,
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag]));
}
