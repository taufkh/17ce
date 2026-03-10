/** @odoo-module **/
/**
 * odes_mail_n_card_scanner — ScannerMixin helpers
 * Migrated from v14 legacy JS mixin -> v16 plain ES module.
 *
 * These functions are called by the patched KanbanController / ListController.
 */
import { _t } from "@web/core/l10n/translation";

/**
 * Handle file input change: auto-submit the hidden upload form.
 * @param {Event} ev
 * @param {Element} contentEl  root element of the controller (.o_content)
 */
export function onAddAttachment(ev, contentEl) {
    const input = ev.currentTarget.querySelector("input.o_input_file");
    if (input && input.value !== "") {
        const form = contentEl.querySelector(".ScannerUploadForm form.o_form_binary_form");
        if (form) form.submit();
    }
}

/**
 * Trigger file input click; create hidden upload form if needed.
 * @param {Element} contentEl  root .o_content element
 * @param {string}  uploadId   unique iframe/form target id
 * @param {Function} renderUploadForm  renders the upload form HTML string
 */
export function onUpload(contentEl, uploadId, renderUploadForm) {
    let formContainer = contentEl.querySelector(".ScannerUploadForm");
    if (!formContainer) {
        const div = document.createElement("div");
        div.innerHTML = renderUploadForm(uploadId);
        contentEl.appendChild(div.firstChild);
        formContainer = contentEl.querySelector(".ScannerUploadForm");
    }
    const fileInput = contentEl.querySelector(".ScannerUploadForm .o_input_file");
    if (fileInput) fileInput.click();
}

/**
 * Callback once the file has been uploaded via iframe.
 * @param {Object} env        OWL env (for rpc / notification)
 * @param {Array}  attachments array of uploaded attachment descriptors
 * @param {Object} context    current action context
 * @param {boolean} isMobile
 */
export async function onFileUploaded(env, attachments, context, isMobile) {
    if (!attachments[0] || !attachments[0].id) {
        env.services.notification.add(_t("An error occurred during the upload"), { type: "danger" });
        return;
    }
    const result = await env.services.orm.call(
        "odes.card.scanner.wizard",
        "card_scanner",
        [[attachments[0].id]],
        { context: { ...context, isMobile } }
    );
    await env.services.action.doAction(result);
}
