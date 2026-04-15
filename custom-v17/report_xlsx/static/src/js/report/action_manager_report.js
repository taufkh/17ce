/** @odoo-module **/

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { getReportUrl } from "@web/webclient/actions/reports/utils";

const reportHandlers = registry.category("ir.actions.report handlers");

reportHandlers.add("report_xlsx.xlsx_handler", async (action, options, env) => {
    if (action.report_type !== "xlsx") {
        return false;
    }

    env.services.ui.block();
    try {
        const userContext = {
            ...env.services.user.context,
            ...(action.context || {}),
        };
        await download({
            url: getReportUrl(action, "xlsx", userContext),
            data: {},
        });
    } finally {
        env.services.ui.unblock();
    }

    if (action.close_on_report_download) {
        return env.services.action.doAction(
            { type: "ir.actions.act_window_close" },
            { onClose: options.onClose }
        );
    }
    if (options.onClose) {
        options.onClose();
    }
    return true;
});
