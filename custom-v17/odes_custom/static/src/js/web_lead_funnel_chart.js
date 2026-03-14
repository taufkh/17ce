/** @odoo-module **/

// NOTE: Highcharts library must be loaded separately
/* global Highcharts */

import { Component, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

class FunnelChart extends Component {
    static template = "FunnelChart";

    setup() {
        this.rpc = useService("rpc");
        this.actionService = useService("action");
        this.CrmFunnelChart = null;

        onMounted(async () => {
            await this._loadFunnelChart();
        });
    }

    async _loadFunnelChart() {
        const self = this;

        // Fetch stage data via JSON-RPC call_kw
        const callbacks = await this.rpc("/web/dataset/call_kw", {
            model: "crm.lead",
            method: "get_lead_stage_data",
            args: [[]],
            kwargs: {},
        });

        const container = this.el.querySelector("#container");
        if (!container) return;

        self.CrmFunnelChart = Highcharts.chart(container, {
            chart: {
                type: "funnel",
                marginRight: 100,
            },
            title: {
                text: _t("Lead/Opportunity Funnel Chart"),
                x: -50,
            },
            plotOptions: {
                series: {
                    dataLabels: {
                        enabled: true,
                        format: "<b>{point.name}</b>({point.y:,.0f})",
                        color:
                            (Highcharts.theme &&
                                Highcharts.theme.contrastTextColor) ||
                            "black",
                        softConnector: true,
                    },
                    neckWidth: "30%",
                    neckHeight: "25%",
                    //  Other available options
                    //  Height: pixels or percent
                    //  Width: pixels or percent
                },
            },
            legend: {
                enabled: false,
            },
            series: [
                {
                    name: _t("Number Of Leads"),
                    data: callbacks,
                },
            ],
        });

        const funnel_container = self.CrmFunnelChart.container;

        // Load the CRM pipeline action and wire up click navigation
        const result = await this.rpc("/web/action/load", {
            action_id: "crm.crm_lead_action_pipeline",
        });

        funnel_container.onclick = function (event) {
            const path = event.composedPath ? event.composedPath() : [];
            if (path[0] && path[0].point !== undefined) {
                const crm_stage = path[0].point.name;
                result.display_name = _t(crm_stage);
                result.view_type = "list";
                result.view_mode = "list";
                result.menu_id = 126;
                result.flags = {
                    search_view: true,
                    display_title: true,
                    pager: true,
                    list: { selectable: true },
                };
                result.views = [
                    [false, "list"],
                    [false, "form"],
                    [false, "kanban"],
                    [false, "calendar"],
                    [false, "pivot"],
                    [false, "graph"],
                ];
                result.domain = [["stage_id.name", "=", _t(crm_stage)]];
                result.filter = true;
                result.target = "current";
                result.context = {};
                self.actionService.doAction(result);
            }
        };
    }
}

registry.category("actions").add("web_lead_funnel_chart.funnel", FunnelChart);
