# -*- coding: utf-8 -*-
{
    'name': 'Odes Mail and Card Scanner',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'sequence': 100,
    'category': 'Uncategorized', 
    'author': 'ODES', 
    'website': 'https://www.odes.com.sg', 
    'description': """
        Odes Mail and Card Scanner
        This module use to customization incoming mail and card scanner.
    """, 
    'depends': [
        'base','web','mail','crm'
    ],

    'data': [
        'data/defaults.xml',
        'security/ir.model.access.csv',
        'wizard/odes_card_scanner_wizard_views.xml',
        'views/partner_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odes_mail_n_card_scanner/static/src/css/style.css',
            'odes_mail_n_card_scanner/static/src/xml/template.xml',
            'odes_mail_n_card_scanner/static/src/js/contact_scanner.js',
            'odes_mail_n_card_scanner/static/src/js/contact.js',
        ],
    },
}
