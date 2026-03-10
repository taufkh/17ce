# -*- coding: utf-8 -*- 

{
    'name': 'ODES Rebrand',
    'category': 'Hidden',
'version': '17.0.1.0.0',    'author': "SGEEDE",
    'website': "dev.odes.com.sg/", 
    'description':
        """
ODES Rebrand Enterprise Web Client.
===========================

This module is ODES Rebran Enterprise Web Client.
        """,
    'depends': ['base', 'web', 'mail', 'auth_signup'],
    'auto_install': True,
    'data': [
        'security/ir.model.access.csv',
#        'data/odes_data.xml',
        'views/webclient_templates.xml',
#        'views/ir_ui_menu_view.xml',
        'views/odes_menu_views.xml',
        'views/auth_signup_login_templates.xml',
        
        'views/odes_rebrand_data_views.xml',
        'wizard/odes_views.xml',
        'wizard/odes_replace_image_views.xml',
    ],
    'license': 'LGPL-3',

    'installable': True,
}
