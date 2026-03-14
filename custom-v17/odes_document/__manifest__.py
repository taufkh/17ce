{
    'name': 'Odes Document',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'category': 'Uncategorized',
    'author': 'SGEEDE',
    'website': 'https://www.sgeede.com', 
    'description': """
        Odes Document
    """, 
    'depends': ['website', 'documents', 'mass_mailing'],
    'data': [
        'security/ir.model.access.csv',
        'views/documents_views.xml',
        'views/mailing_contact_views.xml',
        'views/odes_document_guest.xml',
        'views/documents_add_url_views.xml',
        'views/website_assets.xml',
        'views/website_templates.xml',
    ],

    'installable': True,
}
