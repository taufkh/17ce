{
    'name': 'Approvals (Community Compatibility)',
'version': '17.0.1.0.0',    'category': 'Tools',
    'summary': 'Minimal approvals models for community compatibility',
    'depends': ['mail'],
    'data': [
        'security/approval_security.xml',
        'security/ir.model.access.csv',
        'security/approval_rules.xml',
        'views/approval_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
