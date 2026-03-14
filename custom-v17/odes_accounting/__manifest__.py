# -*- coding: utf-8 -*- 

{
    'name': 'ODES Accounting',
    'category': 'Hidden',
'version': '17.0.1.0.0',    'author': "SGEEDE",
    'website': "dev.odes.com.sg/", 
    'description':
        """
ODES Rebrand Enterprise Web Client.
===========================

This module is ODES Rebran Enterprise Web Client.
        """,
    'depends': ['account', 'sale', 'purchase', 'mccoy_custom', 'account_asset'],
    'auto_install': False,
    'installable': True,
    'data': [
        'report/odes_report_invoice.xml',
        'report/odes_order_confirmation.xml',
        'report/odes_proforma_invoice.xml',
        'report/odes_purchase_order.xml',
        'report/odes_delivery_note.xml',
        'report/odes_commercial_invoice.xml',
        'report/odes_packing_list.xml',
        'security/ir.model.access.csv',
        'views/res_company_view.xml',
        'views/account_move_view.xml',
        'views/account_journal_view.xml',
        'views/res_partner_views.xml',
        # Community-safe: legacy sale form xpath incompatible in v16.
        # Community-safe: legacy purchase form xpath incompatible in v16.
        'views/res_product_views.xml',
        # 'views/stock_picking_view.xml',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/account_assets.xml',
        'wizard/sale_make_invoice_advance_views.xml',
        
#        'report/report_invoice.xml'
    ],
    'license': 'LGPL-3',
}
