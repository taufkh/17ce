{
    'name': 'Website Calendar (Community Compatibility)',
'version': '17.0.1.0.0',    'category': 'Website',
    'summary': 'Minimal appointment model and templates for community compatibility',
    'depends': ['website', 'calendar', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/calendar_data.xml',
        'views/website_calendar_templates.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
