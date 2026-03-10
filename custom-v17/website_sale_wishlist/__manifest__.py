# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Shopper's Wishlist",
    'summary': 'Allow shoppers to enlist products',
    'description': """
Allow shoppers of your eCommerce store to create personalized collections of products they want to buy and save them for future reference.
    """,
    'author': 'Odoo SA',
    'category': 'Website/Website',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'depends': ['website_sale'],
    'data': [
        'security/website_sale_wishlist_security.xml',
        'security/ir.model.access.csv',
        'views/website_sale_wishlist_template.xml',
        'views/snippets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_sale_wishlist/static/src/scss/website_sale_wishlist.scss',
            'website_sale_wishlist/static/src/js/website_sale_wishlist.js',
        ],
    },
    'installable': True,
}
