# -*- coding: utf-8 -*-
{
    'name': "Iconn: Sale",

    'summary': "",

    'description': "",

    'author': "Iconn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customization',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['crm', 'sale', 'account', 'sale_tier_validation', 'sale_project', 'account_commission', 'iconn_account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
