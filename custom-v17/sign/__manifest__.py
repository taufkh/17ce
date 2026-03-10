{
    'name': 'Sign (Community Rebuild)',
'version': '17.0.1.0.0',    'category': 'Tools',
    'summary': 'Community-safe sign-lite template and request workflow',
    'depends': ['mail', 'portal', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/sign_views.xml',
        'views/sign_portal_templates.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
