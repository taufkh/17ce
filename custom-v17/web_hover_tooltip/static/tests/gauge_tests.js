odoo.define('web_hover_tooltip.gauge_tests', function (require) {
"use strict";

var KanbanView = require('web.KanbanView');
var testUtils = require('web.test_utils');

var createView = testUtils.createView;

QUnit.module('fields', {}, function () {

QUnit.module('basic_fields', {
    beforeEach: function () {
        this.data = {
            partner: {
                fields: {
                    int_field: {string: "int_field", type: "integer", sortable: true},
                },
                records: [
                    {id: 1, int_field: 10},
                    {id: 2, int_field: 4},
                ]
            },
        };
    }
}, function () {

    QUnit.module('hover2 widget');

    QUnit.test('basic rendering', async function (assert) {
        assert.expect(1);

        var kanban = await createView({
            View: KanbanView,
            model: 'partner',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div><field name="int_field" widget="hover2"/></div>' +
                '</t></templates></kanban>',
        });

        assert.containsOnce(kanban, '.o_kanban_record:first .oe_gauge canvas',
            "should render the hover2 widget");

        kanban.destroy();
    });

});
});
});
