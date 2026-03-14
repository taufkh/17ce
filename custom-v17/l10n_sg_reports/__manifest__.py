{
    'name': 'Singapore - Accounting Reports (Community Rebuild)',
'version': '17.0.1.0.0',    'category': 'Accounting/Localizations/Reporting',
    'summary': 'Community-safe GST helper and IRAS Audit File export',
    'depends': ['account', 'l10n_sg'],
    'data': [
        'security/ir.model.access.csv',
        'views/iaf_template.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
