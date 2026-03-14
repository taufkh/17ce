# -*- coding: utf-8 -*- 

{
    'name': 'ODES Rebrand Pos',
    'category': 'Hidden',
'version': '17.0.1.0.0',    'author': "SGEEDE",
    'website': "dev.odes.com.sg/", 
    'description':
        """
ODES Rebrand Enterprise Web Client.
===========================

This module is ODES Rebran Enterprise Web Client.
        """,
    'depends': ['base','point_of_sale'],
    'auto_install': False,
    'data': [],
    'assets': {
        'point_of_sale.assets': [
            'odes_design_pos/static/src/js/Chrome.js',
            'odes_design_pos/static/src/xml/Chrome.xml',
            'odes_design_pos/static/src/scss/odes_style.scss',
        ],
    },
    'license': 'LGPL-3',
}
