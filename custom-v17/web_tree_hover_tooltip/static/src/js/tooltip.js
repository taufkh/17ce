/** @odoo-module **/
/**
 * web_tree_hover_tooltip — hover tooltip on list view records
 * Migrated from v14 ListRenderer.include() → v16 patch(ListRenderer.prototype).
 *
 * NOTE: The tooltip reads column index [2] from the row DOM. If the view has
 * a different column order the index must be adjusted accordingly.
 */
import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { onMounted, onWillUnmount } from "@odoo/owl";

patch(ListRenderer.prototype, {
    setup() {
        super.setup(...arguments);

        this._tooltipHandler = null;

        onMounted(() => {
            this._tooltipHandler = (ev) => {
                const link = ev.target.closest("tbody tr td .o_form_uri");
                if (!link) return;
                const row = link.closest("tr");
                if (!row) return;
                const thirdCell = row.children[2];
                const textContent = thirdCell && thirdCell.childNodes[0]
                    ? thirdCell.childNodes[0].textContent
                    : "";
                $(link)
                    .tooltip({
                        title: `<img src='/odes_custom/static/src/img/icon/lead_lt7.png'
                                     style='width:5px;height:45px;'/>
                                <span>${textContent}</span>`,
                        html: true,
                        delay: 0,
                    })
                    .tooltip("show");
            };
            this.el && this.el.addEventListener("mouseover", this._tooltipHandler);
        });

        onWillUnmount(() => {
            if (this._tooltipHandler && this.el) {
                this.el.removeEventListener("mouseover", this._tooltipHandler);
            }
        });
    },
});
