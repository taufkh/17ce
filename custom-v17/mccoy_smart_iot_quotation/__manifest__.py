{
    'name': 'McCoy Smart IOT Quotation',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'category': 'Customize',
    'author': "SGEEDE",
    'website': "dev.odes.com.sg/",
    'summary': 'ODES Smart IOT',
    'description': """
        Customization for McCoy
    """,
    'depends': ['base','iconnexion_custom', 'odes_crm'],
    'data': [
        'security/ir.model.access.csv',
        'data/mccoy_smart_iot_data.xml',
        

        'report/iot_quotation_report.xml',

        'views/product_view.xml',
        # Community-safe fallback: legacy full sale.order form copy is not v17-compatible.
        # 'views/sale_view.xml',
        'views/smart_iot_term_condition_view.xml',
        #'views/crm_lead_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False
}
