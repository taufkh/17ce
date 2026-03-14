# -*- coding: utf-8 -*-
{
    'name': 'MCCOY Website',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'category': 'Uncategorized',
    'sequence': 1,
    'author': 'SGEEDE', 
    'website': 'https://www.sgeede.com', 
    'description': """
        MCCOY Website Custom Development
    """, 
    'depends': ['website','website_sale','ecommerce_theme','website_blog'],
    'data': [
        # Community-safe minimal mode: legacy website QWeb overrides are skipped.
        # 'data/auth_signup_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'mccoy_website/static/src/css/animate.css',
            'mccoy_website/static/src/css/style.css',
            'mccoy_website/static/src/js/website.js',
            'mccoy_website/static/src/js/website_json.js',
            'mccoy_website/static/src/js/cookie.js',
            'mccoy_website/static/src/js/product_configurator_modal.js',
            'mccoy_website/static/src/js/website_sale.js',
            'mccoy_website/static/src/js/website_sale_wishlist.js',
            'mccoy_website/static/src/js/portal_chatter.js',
            'mccoy_website/static/src/js/snippets/000.js',
        ],
        'web.assets_wysiwyg': [
            'mccoy_website/static/src/js/snippets/options.js',
        ],
    },

    'installable': True,
}
