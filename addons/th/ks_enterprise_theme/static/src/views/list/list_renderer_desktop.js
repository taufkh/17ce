/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";

/**
 * Desktop list renderer patch.
 *
 * On community we skip the "Studio editable" and "Promote Studio" dialog
 * logic — those require web_studio (Enterprise only). We still apply the
 * patch so `displayOptionalFields` behaves consistently with Enterprise and
 * the XML template slot is present.
 */
export const patchListRendererDesktop = () => ({
    setup() {
        super.setup(...arguments);
        this.actionService = useService("action");
        // Always false in Community — no Studio available
        this.studioEditable = false;
    },

    isStudioEditable() {
        return this.studioEditable;
    },

    get displayOptionalFields() {
        return super.displayOptionalFields;
    },
});

export const unpatchListRendererDesktop = patch(
    ListRenderer.prototype,
    patchListRendererDesktop()
);
