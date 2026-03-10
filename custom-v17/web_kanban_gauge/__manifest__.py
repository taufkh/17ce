# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Gauge Widget for Kanban',
    'category': 'Hidden',
    'description': """
This widget allows to display gauges using d3 library.
""",
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'web_kanban_gauge/static/src/js/kanban_gauge.js',
        ],
    },
    'auto_install': True,
}
