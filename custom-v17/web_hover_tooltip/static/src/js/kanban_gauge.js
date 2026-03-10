/** @odoo-module **/
/**
 * web_hover_tooltip — Hover2 gauge field widget
 * Migrated from v14 AbstractField.extend() → v16 OWL Component.
 * Registered as field type "hover2".
 */
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useRef, onMounted, onPatched, onWillUnmount, xml } from "@odoo/owl";
import { humanNumber } from "@web/core/utils/numbers";
import { _t } from "@web/core/l10n/translation";

export class Hover2Widget extends Component {
    static template = xml`
        <div class="oe_hover2" t-att-style="props.style" style="position:relative;">
            <canvas t-ref="canvas"/>
            <span class="o_hover2_value"
                  style="text-align:center;position:absolute;left:0;right:0;bottom:6px;font-weight:bold;">
                <t t-esc="humanValue"/>
            </span>
        </div>`;

    static props = { ...standardFieldProps };

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;
        onMounted(() => this._renderGauge());
        onPatched(() => { this._destroyChart(); this._renderGauge(); });
        onWillUnmount(() => this._destroyChart());
    }

    _destroyChart() {
        if (this.chart) { this.chart.destroy(); this.chart = null; }
    }

    get _opts() {
        return this.props.record.activeFields[this.props.name].options || {};
    }

    get gaugeValue() {
        const opts = this._opts;
        let val = this.props.value;
        try { const p = JSON.parse(val); if (Array.isArray(p)) val = p; } catch (e) {}
        let v = Array.isArray(val) && val.length ? val[val.length - 1].value : Number(val) || 0;
        if (opts.gauge_value_field) v = this.props.record.data[opts.gauge_value_field] || 0;
        return v;
    }

    get maxValue() {
        const opts = this._opts;
        let max = opts.max_value || 100;
        if (opts.max_field) max = this.props.record.data[opts.max_field] || max;
        return Math.max(this.gaugeValue, max);
    }

    get humanValue() { return humanNumber(this.gaugeValue, 1); }

    get title() {
        return this._opts.title || this.props.record.activeFields[this.props.name].string || "";
    }

    _renderGauge() {
        const gv = this.gaugeValue;
        const mv = this.maxValue;
        const title = this.title;
        const displayMax = (gv === 0 && mv === 0) ? 1 : mv;

        const config = {
            type: "doughnut",
            data: {
                datasets: [{
                    data: [gv, displayMax - gv],
                    backgroundColor: ["#1f77b4", "#dddddd"],
                    label: title,
                }],
            },
            options: {
                circumference: Math.PI,
                rotation: -Math.PI,
                responsive: true,
                maintainAspectRatio: false,
                cutout: "70%",
                plugins: {
                    title: { display: true, text: title, padding: 4 },
                    tooltip: {
                        displayColors: false,
                        callbacks: {
                            label: (ctx) => ctx.dataIndex === 0
                                ? String(_t("Value: ")) + gv
                                : String(_t("Max: ")) + mv,
                        },
                    },
                },
                layout: { padding: { bottom: 5 } },
            },
        };

        const canvas = this.canvasRef.el;
        if (canvas) this.chart = new Chart(canvas.getContext("2d"), config);
    }
}

registry.category("fields").add("hover2", Hover2Widget);
