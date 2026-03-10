/** @odoo-module **/
/**
 * odes_mail_n_card_scanner — OCR scan button for Contacts list/kanban
 * Migrated from v14 viewRegistry.add() with Controller.extend()
 *                 → v16 registry.category("views").add() with subclassed controllers.
 *
 * The "OCR" button is added by registering custom view types (js_class in XML)
 * with controllers that extend the base ones.  The button injects a hidden file
 * input form and calls odes.card.scanner.wizard.card_scanner on upload.
 */
import { registry } from "@web/core/registry";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";
import { uniqueId } from "@web/core/utils/functions";
import { onFileUploaded } from "./contact_scanner";
import { onMounted, onWillUnmount } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

// ----- Shared scanner hook --------------------------------------------------

function useOcrScanner() {
    const uploadId = uniqueId("ocr_scanner_");
    const actionService = useService("action");
    const notificationService = useService("notification");
    const orm = useService("orm");

    onMounted(() => {
        const handler = (...args) => {
            const attachments = Array.prototype.slice.call(args, 1);
            const context = {};
            onFileUploaded(
                { services: { notification: notificationService, orm, action: actionService } },
                attachments,
                context,
                false
            );
        };
        $(window).on(uploadId, handler);
        this._ocrCleanup = () => $(window).off(uploadId, handler);
    });

    onWillUnmount(() => this._ocrCleanup && this._ocrCleanup());

    function getUploadFormHtml(uid) {
        return `<div class="d-none ScannerUploadForm">
            <div class="o_hidden_input_file">
                <form class="o_form_binary_form" target="${uid}"
                      method="post" enctype="multipart/form-data"
                      action="/odes_directly_scan_contact">
                    <input type="hidden" name="csrf_token"/>
                    <input type="hidden" name="callback" value="${uid}"/>
                    <input type="file" class="o_input_file" name="ufile"
                           multiple="0" accept="image/*" capture="camera"/>
                    <input type="hidden" name="model" value="odes.card.scanner.wizard"/>
                    <input type="hidden" name="id" value="0"/>
                </form>
                <iframe id="${uid}" name="${uid}" style="display:none"/>
            </div>
        </div>`;
    }

    return {
        uploadId,
        onOcrClick(ev) {
            const root = ev.currentTarget.closest(".o_action_manager") || document.body;
            if (!root.querySelector(".ScannerUploadForm")) {
                root.insertAdjacentHTML("beforeend", getUploadFormHtml(uploadId));
                root.querySelector(".ScannerUploadForm form input[name='csrf_token']").value =
                    odoo.csrf_token || "";
                root.querySelector(".ScannerUploadForm .o_input_file").addEventListener(
                    "change",
                    (e) => {
                        const form = root.querySelector(".ScannerUploadForm form");
                        if (e.target.value && form) form.submit();
                    }
                );
            }
            root.querySelector(".ScannerUploadForm .o_input_file").click();
        },
    };
}

// ----- Custom controllers ---------------------------------------------------

class ScannerKanbanController extends KanbanController {
    setup() {
        super.setup(...arguments);
        const scanner = useOcrScanner.call(this);
        this.onOcrClick = scanner.onOcrClick;
    }
}

class ScannerListController extends ListController {
    setup() {
        super.setup(...arguments);
        const scanner = useOcrScanner.call(this);
        this.onOcrClick = scanner.onOcrClick;
    }
}

// ----- Custom view templates (OWL t-inherit adds the OCR button) -----------
// Actual templates are defined in static/src/xml/template.xml
ScannerKanbanController.template = "odes_mail_n_card_scanner.ScannerKanbanView";
ScannerListController.template = "odes_mail_n_card_scanner.ScannerListView";

// ----- Register custom views ------------------------------------------------

registry.category("views").add("res_partner_kanban_view_scan", {
    ...kanbanView,
    Controller: ScannerKanbanController,
});

registry.category("views").add("res_partner_tree_view_scan", {
    ...listView,
    Controller: ScannerListController,
});
