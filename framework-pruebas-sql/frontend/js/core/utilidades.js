export function escapeHTML(str) {
    if (str === null || str === undefined) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export let modalGeneralAction = null;
export let modalGeneralId = null;
let modalGeneralInst = null;

export function getModalGeneralInst() {
    if (!modalGeneralInst) {
        modalGeneralInst = new bootstrap.Modal(document.getElementById("modalGeneral"));
    }
    return modalGeneralInst;
}

export function abrirModalGeneral(title, html, actionType, id = null) {
    document.getElementById("modalGeneralTitle").innerText = title;
    document.getElementById("modalGeneralBody").innerHTML = html;
    modalGeneralAction = actionType;
    modalGeneralId = id;
    document.getElementById("modalGeneralSubmit").disabled = false;
    getModalGeneralInst().show();
}

export function hideModalGeneral() {
    getModalGeneralInst().hide();
}
