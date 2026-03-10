##############################################################################
#
#       Copyright © SUREKHA TECHNOLOGIES PRIVATE LIMITED, 2020.
#
#	    You can not extend,republish,modify our code,app,theme without our
#       permission.
#
#       You may not and you may not attempt to and you may not assist others
#       to remove, obscure or alter any intellectual property notices on the
#       Software.
#
##############################################################################
{
    'name': 'E-commerce Theme',
'version': '17.0.1.0.0',    'sequence': 102,
    'author': 'Surekha Technologies Pvt. Ltd.',
    'description': "Multi Purpose, Responsive with advance new features in the e-commerce theme.",
    'summary': "Multi Purpose, Responsive with advance new features in the e-commerce theme.",
    'category': 'Theme/Ecommerce',
    'website': 'https://www.surekhatech.com',
    'depends': ['website_sale', 'mass_mailing_sale', 'website_mass_mailing', 'website_sale_wishlist',
                'website_sale_comparison','product'],
    'data': [
        'security/product_brand_security.xml',
        'security/ir.model.access.csv',
        'data/ecommerce_mass_mailing_data.xml',
        'views/product_brand_view.xml',
        'views/product_template_view.xml',
        # Community-safe minimal mode: legacy website templates/snippets are skipped.
    ],
    'assets': {
        'web.assets_frontend': [
            'ecommerce_theme/static/src/css/st_ecommerce_theme.css',
            'ecommerce_theme/static/lib/owl/owl.carousel.css',
            'ecommerce_theme/static/lib/owl/owl.carousel.min.js',
            'ecommerce_theme/static/src/js/st_ecommerce_theme_header.js.legacy',
            'ecommerce_theme/static/src/js/st_ecommerce_theme_product.js.legacy',
            'ecommerce_theme/static/src/js/st_ecommerce_theme_cart.js.legacy',
            'ecommerce_theme/static/src/js/st_ecommerce_theme_popular_product.js.legacy',
        ],
        'web.assets_backend': [
            'ecommerce_theme/static/src/js/st_ecommerce_theme.editor.js.legacy',
        ],
    },
    'images': [
        'images/ecommerce_theme.png',
        'static/description/ecommerce_screenshot.png'
    ],
    'application': True,
    'price': 49.00,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'live_test_url': 'http://demoodoo.surekhatech.com/v13/web?db=odoo_13_st_ecommerce_theme',
}
