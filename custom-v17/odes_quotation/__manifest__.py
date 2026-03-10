# -*- coding: utf-8 -*-
{
    'name': 'ODES Quotation',
'version': '17.0.1.0.0',    'category': 'Extra Tools',
    'summary': '',
    'description': '''
Odes Quotation Customization.
===========================
This module is using for customization of Quotation / Sales Module.



**Installed on :** IP_SERVER | DB NAME :

- 203.127.198.245 | ODES_PRODUCTION

- 203.127.198.229 | ODES_PRODUCTION_COPY
    ''',
    'author': "SGEEDE",
    'website': "https://www.sgeede.com",
    'depends': ['base', 'sale', 'sale_crm', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/report_paperformat.xml',
        'data/odes_data.xml',
        'data/ir_sequence_data.xml',
        'report/report_views.xml',
        'report/report_service_quotation.xml',
        'views/sale_views.xml',
        'views/sale_portal_templates.xml',
        'views/sale_order_template_views.xml',
        'views/res_company_views.xml',
        # v16: report_templates.xml removed — assets declared in 'assets' dict below
    ],
    'assets': {
        'web.report_assets_common': [
            'odes_quotation/static/src/css/report.css',
        ],
        'web.assets_frontend': [
            'odes_quotation/static/src/scss/sale_portal.scss',
        ],
        'web_editor.assets_wysiwyg': [
            'odes_quotation/static/src/css/custom.css',
        ],
    },
    'license': 'OPL-1',
    'demo': [],
}