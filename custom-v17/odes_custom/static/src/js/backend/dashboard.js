/** @odoo-module **/

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

// Google Analytics integration removed - not supported in v16

const COLORS = ["#1f77b4", "#aec7e8"];

const FORMAT_OPTIONS = {
    // allow to decide if utils.human_number should be used
    humanReadable: function (value) {
        return Math.abs(value) >= 1000;
    },
    // with the choices below, 1236 is represented by 1.24k
    minDigits: 1,
    decimals: 2,
    // avoid comma separators for thousands in numbers when human_number is used
    formatterCallback: function (str) {
        return str;
    },
};

class Dashboard extends Component {
    static template = "odes_custom.DashboardMain";

    setup() {
        this.rpc = useService("rpc");
        this.actionService = useService("action");

        this.DATE_FORMAT = "DD/MM/YYYY";
        this.date_range = "week"; // possible values: 'week', 'month', 'year'
        this.date_from = moment.utc().subtract(1, "week");
        this.date_to = moment.utc();

        this.graphs = [];
        this.chartIds = {};
        this.chart = null;

        this.state = useState({
            data: {},
            active_lead: 0,
            active_lead_l7: 0,
            active_lead_g7: 0,
            active_opportunity: 0,
            opportunity_revenue: 0,
            active_opportunity_l7: 0,
            opportunity_revenue_l7: 0,
            active_opportunity_g7: 0,
            opportunity_revenue_g7: 0,
            outstanding_won: 0,
            outstanding_lost: 0,
            funnel_data: [],
            fname1: "", fcount1: 0, fmoun1: 0,
            fname2: "", fcount2: 0, fmoun2: 0,
            fname3: "", fcount3: 0, fmoun3: 0,
            fname4: "", fcount4: 0, fmoun4: 0,
            fname5: "", fcount5: 0, fmoun5: 0,
            fname6: "", fcount6: 0, fmoun6: 0,
            fname7: "", fcount7: 0, fmoun7: 0,
        });

        this.user_id = false;
        this.company_id = false;

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.fetch_data();
        });

        onMounted(() => {
            this.el.parentElement && this.el.parentElement.classList.add("oe_background_grey");
        });
    }

    /**
     * Fetches dashboard data
     */
    async fetch_data() {
        const result = await this.rpc("/odes_custom/fetch_dashboard_data", {
            user: this.user_id,
            company: this.company_id,
        });
        if (result) {
            Object.assign(this.state, {
                data: result,
                active_lead: result.active_lead,
                active_lead_l7: result.active_lead_l7,
                active_lead_g7: result.active_lead_g7,
                active_opportunity: result.active_opportunity,
                opportunity_revenue: result.opportunity_revenue,
                active_opportunity_l7: result.active_opportunity_l7,
                opportunity_revenue_l7: result.opportunity_revenue_l7,
                active_opportunity_g7: result.active_opportunity_g7,
                opportunity_revenue_g7: result.opportunity_revenue_g7,
                outstanding_won: result.outstanding_won,
                outstanding_lost: result.outstanding_lost,
                funnel_data: result.funnel_data,
                fname1: result.fname1, fcount1: result.fcount1, fmoun1: result.fmoun1,
                fname2: result.fname2, fcount2: result.fcount2, fmoun2: result.fmoun2,
                fname3: result.fname3, fcount3: result.fcount3, fmoun3: result.fmoun3,
                fname4: result.fname4, fcount4: result.fcount4, fmoun4: result.fmoun4,
                fname5: result.fname5, fcount5: result.fcount5, fmoun5: result.fmoun5,
                fname6: result.fname6, fcount6: result.fcount6, fmoun6: result.fmoun6,
                fname7: result.fname7, fcount7: result.fcount7, fmoun7: result.fmoun7,
            });
        }
    }

    /**
     * Renders a Chart.js line chart into a given container selector.
     * div_to_display: CSS selector string (e.g. '#lead_chart_container')
     * chart_values:   array of {key, values: [[date, val], ...]} objects
     * chart_id:       id to assign to the canvas element
     */
    render_graph(div_to_display, chart_values, chart_id) {
        const self = this;
        const container = this.el.querySelector(div_to_display);
        if (!container) return;

        container.innerHTML = "";
        const canvasContainer = document.createElement("div");
        canvasContainer.className = "o_graph_canvas_container";
        const canvas = document.createElement("canvas");
        canvas.id = chart_id;
        canvasContainer.appendChild(canvas);
        container.appendChild(canvasContainer);

        const labels = chart_values[0].values.map(function (date) {
            return moment(date[0], "YYYY-MM-DD", "en");
        });

        const datasets = chart_values.map(function (group, index) {
            return {
                label: group.key,
                data: group.values.map(function (value) {
                    return value[1];
                }),
                dates: group.values.map(function (value) {
                    return value[0];
                }),
                fill: false,
                borderColor: COLORS[index],
            };
        });

        const ctx = canvas;
        this.chart = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: datasets,
            },
            options: {
                legend: {
                    display: false,
                },
                maintainAspectRatio: false,
                scales: {
                    yAxes: [{
                        type: "linear",
                        ticks: {
                            beginAtZero: true,
                            callback: this.formatValue.bind(this),
                        },
                    }],
                    xAxes: [{
                        ticks: {
                            callback: function (momentObj) {
                                return momentObj.format(self.DATE_FORMAT);
                            },
                        },
                    }],
                },
                tooltips: {
                    mode: "index",
                    intersect: false,
                    bodyFontColor: "rgba(0,0,0,1)",
                    titleFontSize: 13,
                    titleFontColor: "rgba(0,0,0,1)",
                    backgroundColor: "rgba(255,255,255,0.6)",
                    borderColor: "rgba(0,0,0,0.2)",
                    borderWidth: 2,
                    callbacks: {
                        title: function (tooltipItems, data) {
                            return data.datasets[0].label;
                        },
                        label: function (tooltipItem, data) {
                            const momentObj = data.labels[tooltipItem.index];
                            const date =
                                tooltipItem.datasetIndex === 0
                                    ? momentObj
                                    : momentObj.subtract(1, self.date_range);
                            return (
                                date.format(self.DATE_FORMAT) +
                                ": " +
                                self.formatValue(tooltipItem.yLabel)
                            );
                        },
                        labelColor: function (tooltipItem, chart) {
                            const dataset = chart.data.datasets[tooltipItem.datasetIndex];
                            return {
                                borderColor: dataset.borderColor,
                                backgroundColor: dataset.borderColor,
                            };
                        },
                    },
                },
            },
        });
    }

    async onSubmitClick() {
        const userSelect = this.el.querySelector("#user_selection");
        const companySelect = this.el.querySelector("#company_selection");
        this.user_id = userSelect ? userSelect.value : false;
        this.company_id = companySelect ? companySelect.value : false;

        await this.fetch_data();
    }

    onDashboardAction(ev) {
        ev.preventDefault();
        const action = ev.currentTarget.dataset.action;
        const additional_context = {
            user_ctx: this.user_id,
            company_ctx: this.company_id,
        };
        this.actionService.doAction(action, {
            additional_context: additional_context,
        });
    }

    onDashboardActionForm(ev) {
        ev.preventDefault();
        const el = ev.currentTarget;
        this.actionService.doAction({
            name: el.getAttribute("name"),
            res_model: el.dataset.resModel,
            res_id: parseInt(el.dataset.resId, 10) || false,
            views: [[false, "form"]],
            type: "ir.actions.act_window",
        });
    }

    onDateRangeButton(date_range) {
        if (date_range === "week") {
            this.date_range = "week";
            this.date_from = moment().subtract(1, "weeks");
        } else if (date_range === "month") {
            this.date_range = "month";
            this.date_from = moment().subtract(1, "months");
        } else if (date_range === "year") {
            this.date_range = "year";
            this.date_from = moment().subtract(1, "years");
        } else {
            console.log("Unknown date range. Choose between [week, month, year]");
            return;
        }
        this.fetch_data();
    }

    // Utility: format a float value for display on chart axes
    formatValue(value) {
        const absVal = Math.abs(value);
        if (absVal >= 1000000) {
            return (value / 1000000).toFixed(2) + "M";
        } else if (absVal >= 1000) {
            return (value / 1000).toFixed(2) + "k";
        }
        return parseFloat(value).toFixed(2);
    }

    getValue(d) {
        return d[1];
    }
}

registry.category("actions").add("odes_dashboard", Dashboard);
