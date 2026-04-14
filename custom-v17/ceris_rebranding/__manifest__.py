# -*- coding: utf-8 -*-
{
    'name': 'CERIS Rebranding',
    'summary': 'Remove Odoo branding and replace it with CERIS',
    'version': '17.0.1.0.0',
    'category': 'Hidden',
    'license': 'LGPL-3',
    'author': 'iCONN',
    'depends': ['web'],
    'data': [
        'data/res_partner_data.xml',
        'data/ir_ui_view_data.xml',
    ],
    'assets': {
        'web.assets_common': [
            'ceris_rebranding/static/src/js/ceris_rebranding.js',
            'ceris_rebranding/static/src/scss/ceris_rebranding.scss',
        ],
        'web.assets_backend': [
            'ceris_rebranding/static/src/xml/res_config_edition.xml',
        ],
        'web.assets_frontend': [
            'ceris_rebranding/static/src/js/ceris_rebranding.js',
            'ceris_rebranding/static/src/scss/ceris_rebranding.scss',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
}
