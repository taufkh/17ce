/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { GraphRenderer } from "@web/views/graph/graph_renderer";

// Custom ODES brand color palette (replaces the default Odoo colors)
const COLORS = [
    "#0062B9", "#27AFEE", "#EEBF00", "#FF8000", "#FF4F61", "#A30000", "#7028A9",
    "#9E50FF", "#00B431", "#00E9C2", "#3A3A3A", "#F6ADC6", "#CAE2BC", "#498C8A",
    "#FFE6A7", "#DCCCBB", "#EAB464", "#A7754D", "#C36F09", "#9EDAE5",
];

patch(GraphRenderer.prototype, {
    _getColor(index) {
        return COLORS[index % COLORS.length];
    },
});
