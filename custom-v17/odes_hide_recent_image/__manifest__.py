# -*- coding: utf-8 -*-
{
    'name': 'ODES Hide Recent Image',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'sequence': 1,
    'category': 'Uncategorized', 
    'author': 'SGEEDE', 
    'website': 'https://www.sgeede.com', 
    'description': """
        This module is using for hide images in the recent image history features
    """, 
    'depends': ['web'],
    'data': [],
    # v16: assets are declared in __manifest__.py, not via template xpath
    'assets': {
        'web.assets_backend': [
            'odes_hide_recent_image/static/src/css/odes_backend_style.css',
        ],
        'web.assets_frontend': [
            'odes_hide_recent_image/static/src/css/odes_backend_style.css',
        ],
    },
    'demo': [],
    'auto_install': True,
}
