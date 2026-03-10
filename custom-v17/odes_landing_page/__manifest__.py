# -*- coding: utf-8 -*- 

{
    'name': 'Odes Landing Page Website',
    'category': 'Hidden',
'version': '17.0.1.0.0',    'author': "SGEEDE",
    'website': "https://www.sgeede.com",
    'description':
        """
Odes Landing Page Website.
===========================

This module is Odes to add new page (Landing Page). \n

        """,
    'depends': ['base','website'],
    'auto_install': False,
    'data': [
        'views/website_views.xml',
        'views/webclient_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'odes_landing_page/static/src/css/landing_page.css',
            'odes_landing_page/static/src/js/website.js',
        ],
    },
    'license': 'LGPL-3',
}
