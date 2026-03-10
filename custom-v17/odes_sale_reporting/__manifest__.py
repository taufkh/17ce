# -*- coding: utf-8 -*-
{
    'name': 'Odes Sale Reporting',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'sequence': 1,
    'category': 'Uncategorized', 
    'author': 'SGEEDE', 
    'website': 'https://www.sgeede.com', 
    'description': """
        Odes Sale Reporting
    """, 
    'depends': [
        'base', 'sale', 'purchase', 'odes_quotation', 'stock', 'mccoy_custom'
    ],
    'data': [
        'security/ir.model.access.csv',
        # v16: views/assets.xml removed — assets declared in 'assets' dict below

        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/stock_views.xml',
        'report/odes_sale_tracker_report_views.xml',
        'report/odes_sale_tracker_product_report_views.xml',
        'report/odes_sale_billing_detail_report_views.xml',
        'report/odes_yearly_sale_summary_report_views.xml',
        'report/odes_yearly_billing_summary_report_views.xml',
        
        'wizard/odes_sale_link_po_to_supplier_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odes_sale_reporting/static/src/css/custom.css',
        ],
    },
}
