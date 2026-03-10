# -*- coding: utf-8 -*- 

{
    'name': 'Odes API',
    'category': 'Uncategorized',
'version': '17.0.1.0.0',    'author': "SGEEDE",
    'website': "https://odes.com.sg", 
    'description':
        """
Odes API.
===========================

This module is Odes API.
        """,
    'depends': ['base','mail'],
    'auto_install': False,
    'data': [
        'security/ir.model.access.csv',
        'views/webclient_templates.xml',
        'views/config_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odes_api/static/css/custom.css',
        ],
    },
    'license': 'LGPL-3',
}
