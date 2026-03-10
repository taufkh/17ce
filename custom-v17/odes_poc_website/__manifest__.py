# -*- coding: utf-8 -*-
{
    'name': 'Odes POC Website',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'sequence': 1,
    'category': 'Uncategorized', 
    'author': 'SGEEDE', 
    'website': 'https://www.sgeede.com', 
    'description': """
        Odes POC Website Development
    """, 
    'depends': [
        'website', 'website_blog', 'website_crm', 'web_editor'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/odes_data.xml',
        'views/company_view.xml',
        'views/res_config_settings_views.xml',
        # 'views/assets.xml',  # legacy frontend_layout xpath not compatible in v16
        # 'views/website_templates.xml',  # legacy template overrides target removed xmlids in v16
        'views/crm_team_view.xml',
        'views/res_company_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'odes_poc_website/static/src/css/custom.css',
            'odes_poc_website/static/src/js/js-cookie.js',
            'odes_poc_website/static/src/js/custom.js',
            'odes_poc_website/static/src/snippets/s_website_form/000.js',
        ],
    },
    'demo': []
}
