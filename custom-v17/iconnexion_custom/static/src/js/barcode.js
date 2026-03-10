/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { onMounted, onWillUnmount } from "@odoo/owl";

/**
 * Barcode scanner keyboard UX for stock.move.line.
 *
 * v14 behaviour (now removed):
 *   AbstractField.include({ _onKeydown }) patched ENTER to call
 *   trigger_up('navigation_move', { direction: 'next' }) on stock.move.line,
 *   then always trigger_up('navigation_move', { direction: 'next_line' }).
 *
 * v16 approach:
 *   patch ListRenderer to intercept ENTER at capture phase when the list's
 *   resModel is 'stock.move.line'.  Instead of moving to the next row
 *   (Odoo default), ENTER advances to the next focusable input within the
 *   same row.  When already on the last input of a row it moves focus to
 *   the first input of the next row, mimicking the barcode-scanner tab-stop
 *   workflow.
 */
patch(ListRenderer.prototype, {
    setup() {
        super.setup(...arguments);

        if (this.props.list?.resModel === "stock.move.line") {
            onMounted(() => {
                this._barcodeKeydownHandler = (ev) => this._onBarcodeEnter(ev);
                this.el?.addEventListener("keydown", this._barcodeKeydownHandler, true);
            });
            onWillUnmount(() => {
                this.el?.removeEventListener("keydown", this._barcodeKeydownHandler, true);
            });
        }
    },

    /**
     * Intercept the ENTER key inside an editable stock.move.line list.
     * Navigates to the next focusable field in the row (or the first field
     * of the next row when at the row's last input).
     *
     * @param {KeyboardEvent} ev
     */
    _onBarcodeEnter(ev) {
        if (ev.key !== "Enter" || ev.repeat || ev.isComposing) {
            return;
        }
        const focused = document.activeElement;
        if (!focused || !this.el.contains(focused)) {
            return;
        }
        const row = focused.closest("tr");
        if (!row) {
            return;
        }

        // All enabled, non-readonly inputs inside this row
        const inputs = [
            ...row.querySelectorAll(
                "input:not([disabled]):not([readonly])," +
                "select:not([disabled])," +
                "textarea:not([disabled]):not([readonly])"
            ),
        ];
        const idx = inputs.indexOf(focused);
        if (idx === -1) {
            return;
        }

        ev.preventDefault();
        ev.stopPropagation();

        if (idx < inputs.length - 1) {
            // Move to next field in the same row
            inputs[idx + 1].focus();
        } else {
            // Last field in row → move to first field of the next row
            const nextRow = row.nextElementSibling;
            const firstInput = nextRow?.querySelector(
                "input:not([disabled]):not([readonly])," +
                "select:not([disabled])," +
                "textarea:not([disabled]):not([readonly])"
            );
            if (firstInput) {
                firstInput.focus();
            }
        }
    },
});
