# -*- coding: utf-8 -*-
{
    'name': 'Odes Social Media Webhooks',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'sequence': 100,
    'category': 'Uncategorized', 
    'author': 'SGEEDE', 
    'website': 'https://www.sgeede.com', 
    'description': """
        Odes Social Media Webhooks Development
        This module use to send data Callback from Facebook/Instagram to Multi url
    """, 
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv', 
        'views/odes_social_media_webhooks_views.xml',
    ]
}
