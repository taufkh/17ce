{
    'name': 'Documents (Community Compatibility)',
'version': '17.0.1.0.0',    'category': 'Productivity',
    'summary': 'Minimal documents models and routes for community compatibility',
    'depends': ['mail', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/documents_views.xml',
        'views/documents_templates.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
