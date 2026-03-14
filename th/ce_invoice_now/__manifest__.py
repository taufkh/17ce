# -*- coding: utf-8 -*-

{
    'name': 'CE Invoice Now',
'version': '17.0.1.0.0',    'category': 'Accounting/Accounting',
    'summary': 'InvoiceNow Datapost integration for Odoo Community',
    'depends': [
        'account',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'wizard/send_invoice_views.xml',
        'views/account_move_views.xml',
        'views/invoice_now_configuration_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
