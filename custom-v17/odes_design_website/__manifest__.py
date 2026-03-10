# -*- coding: utf-8 -*- 

{
    'name': 'Odes Rebrand Website',
    'category': 'Hidden',
'version': '17.0.1.0.0',    'author': "SGEEDE",
    'website': "https://www.sgeede.com",
    'description':
        """
Odes Rebrand Enterprise Website.
===========================

This module is Odes Rebran Enterprise Website Include. \n
- Live Chat \n
- Website



**Installed on :** IP_SERVER | DB NAME :

- 203.127.198.245 | ODES_PRODUCTION

- 203.127.198.229 | ODES_PRODUCTION_COPY
        """,
    'depends': ['base','website','im_livechat'],
    'auto_install': True,
    'data': [
        'views/snippets/s_facebook_page.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'odes_design_website/static/src/scss/odes_website_style.css',
        ],
    },
    'license': 'LGPL-3',
}
