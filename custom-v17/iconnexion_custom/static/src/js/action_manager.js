/** @odoo-module **/
/**
 * iconnexion_custom — xlsx report download action handler
 * Migrated from v14 ActionManager.include() → v16 action_handlers registry.
 *
 * In v14 the handler checked `action.report_type === 'xlsx'` inside a patched
 * ActionManager._handleAction.  In v16 we register against the action type
 * 'ir_actions_xlsx_download'.  The server-side report action must set
 * type='ir_actions_xlsx_download' (not just report_type='xlsx').
 */
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

const actionHandlers = registry.category("action_handlers");

/**
 * Download an xlsx report via the /xlsx_reports endpoint.
 * Triggered when action.type === 'ir_actions_xlsx_download'.
 *
 * @param {Object} env    - OWL environment (env.services.ui, etc.)
 * @param {Object} action - the action object (action.data sent as POST body)
 */
async function xlsxDownloadHandler(env, action) {
    env.services.ui.block();
    try {
        await download({
            url: "/xlsx_reports",
            data: action.data,
        });
    } finally {
        env.services.ui.unblock();
    }
}

actionHandlers.add("ir_actions_xlsx_download", xlsxDownloadHandler);
