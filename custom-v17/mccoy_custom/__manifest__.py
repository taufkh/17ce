# -*- coding: utf-8 -*-
{
    'name': 'MCCOY Custom',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'category': 'Uncategorized',
    'sequence': 1,
    'author': 'SGEEDE', 
    'website': 'https://www.sgeede.com', 
    'description': """
        MCCOY Custom Development
    """, 
    'depends': ['product','website_sale','ecommerce_theme','purchase'],
    'data': [
        'security/ir.model.access.csv',
        'security/mccoy_security.xml',
#        'views/product_views.xml',
        'views/mccoy_subscribe_views.xml',
        'views/blog_views.xml',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/website_views.xml',
        'wizard/mccoy_special_export_wizard_views.xml',
        # 'data/auth_signup_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mccoy_custom/static/src/css/style.css',
        ],
    },

    'installable': True,
}
