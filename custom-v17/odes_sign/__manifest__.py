{
    'name': 'ODES Sign',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'category': 'Customize',
    'author': "SGEEDE",
    'website': "dev.odes.com.sg/",
    'summary': 'ODES Sign',
    'description': """
Customization for skinlab
    """,
    'depends': ['base', 'purchase', 'odes_accounting', 'hr_expense', 'account'],
    'data': [
        'data/data.xml',
        'data/cron.xml',
        'data/mail_template.xml',
        # Community-safe: stock_barcode JS override is skipped.
        'security/ir.model.access.csv',
        'report/odes_purchase_order.xml',
        'report/report_sale_order.xml',
        'report/odes_order_confirmation.xml',
        'report/odes_tax_invoice_report.xml',
        'report/odes_proforma_invoice_report.xml',
        'report/odes_delivery_note_report.xml',
        'report/report_mccoy_tax_invoice_usd.xml',
        'security/sign_security.xml',
#        'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/company_views.xml',
        'views/stock_picking_views.xml',
        # Community-safe: inherits odes_custom attachment form (not guaranteed installed in this wave).
        # Community-safe: approvals view extension is skipped.
        'views/expense_views.xml',
        # Community-safe: employee update legacy views depend on odes_hr2_custom fields/groups.
        'wizard/wizard_res_partner_views.xml',
        # Community-safe: requires account_followup action XMLID.
        'wizard/wizard_request_purchase_order_views.xml',
        'views/account_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False
}
