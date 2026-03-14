# -*- coding: utf-8 -*-
{
    "name": "iConnexion McCoy Custom",
    "version": "17.0.1.0.0",
    "category": "Customize",
    "summary": "iConnexion McCoy",
    "description": """
iConnexion McCoy modified features.
    """,
    "author": "SGEEDE",
    "support": "support@sgeede.com",
    "maintainer": "SGEEDE",
    "website": "https://www.sgeede.com",
    "depends": ["base", "crm", "sale", "account", "delivery_compat", "odes_quotation", "iconnexion_custom", "odes_accounting", "mccoy_custom", "odes_custom", "odes_sign"],
    "data": [
        "security/ir.model.access.csv",   
        'security/iconnexion_mccoy_security.xml',

        'data/data.xml',
        'data/ir_sequence_data.xml',
        # Community-safe: account.tax.report data requires account_reports.

        'views/report_templates.xml',
        # Community-safe: account_reports-specific financial report extension is skipped.
        'views/sale_views.xml',
        # Community-safe: account.move inherited form relies on fields unavailable in this stack.
        'views/crm_lead_views.xml',
        # Community-safe: partner delivery-method customizations are skipped.
        # Community-safe: product inherited view depends on unavailable mccoy_custom XML IDs.
        # Community-safe: delivery carrier extension is skipped.
        # Community-safe: stock picking carrier view depends on delivery module.
        # Community-safe: purchase inherited view depends on removed odes_accounting views.
        'views/stock_move_views.xml',
        'views/res_currency_views.xml',
        # Community-safe: settings view includes delivery-carrier domains not valid in this stack.
        'views/res_users_views.xml',
        'views/mailing_views.xml',
        'views/stock_location_views.xml',

        'report/report_iconnexion_purchase_order.xml',
        'report/report_iconnexion_commercial_invoice.xml',
        'report/report_iconnexion_delivery_order.xml',
        'report/report_iconnexion_proforma_invoice.xml',
        'report/report_iconnexion_tax_invoice.xml',
        'report/report_quotation_mccoy.xml',
        'report/report_sale_order_iconnexion.xml',
        'report/odes_commercial_invoice.xml',
        'report/odes_delivery_note.xml',
        'report/odes_order_confirmation.xml',
        'report/odes_packing_list.xml',
        'report/odes_purchase_order.xml',
        'report/report_sale_order.xml',
        'report/report_sale_order_sgd.xml',
        'report/report_mccoy_tax_invoice_usd.xml',
        'report/report_iconnexion_debit_note.xml',
        'report/report_iconnexion_credit_note.xml',
        'report/report_iconnexion_mccoy_invoice.xml',
        'report/report_certification_of_conformance_harwin.xml',
        'report/report_sample_request_harwin.xml',
        'report/report_iconnexion_packing_weight_list.xml',
        'report/report_iconnexion_label.xml',
        'report/report_iconnexion_commercial_invoice_without_mpn.xml',
        # Community-safe: missing report file skipped.
        # Community-safe: missing report file skipped.
        # Community-safe: missing report file skipped.
        
        'wizard/wizard_request_purchase_order.xml',
        'wizard/crm_lead_to_opportunity_views.xml',
        'wizard/update_po_so_linkage.xml',
        # Community-safe: missing wizard files skipped.


    ],
    "images": [],
    'license': 'OPL-1',
    "demo": [],

    'installable': True,
}
