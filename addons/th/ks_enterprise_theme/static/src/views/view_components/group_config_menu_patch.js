/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { GroupConfigMenu } from "@web/views/view_components/group_config_menu";

/**
 * GroupConfigMenu patch for ks_enterprise_theme.
 *
 * Adds canEditAutomations permission and the "Automations" group config item.
 * On Community, openAutomations calls _openAutomations() only if base_automation
 * is installed; otherwise the action is silently skipped (no Studio dialog).
 */
patch(GroupConfigMenu.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
    },

    get permissions() {
        const permissions = super.permissions;
        Object.defineProperty(permissions, "canEditAutomations", {
            get: () => user.isAdmin,
            configurable: true,
        });
        return permissions;
    },

    async openAutomations() {
        if (typeof this._openAutomations === "function") {
            // base_automation is installed — open it directly
            return this._openAutomations();
        }
        // base_automation not installed — do nothing (Community, no Studio)
    },
});

registry.category("group_config_items").add(
    "open_automations",
    {
        label: _t("Automations"),
        method: "openAutomations",
        isVisible: ({ permissions }) => permissions.canEditAutomations,
        class: "o_column_automations",
        icon: "fa-magic",
    },
    { sequence: 25, force: true }
);
