# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# {
#     'name': 'Odes Outlook Calendar',
#     17.0.1.0.0',
#     'category': 'Productivity',
#     'description': "",
#     'depends': ['microsoft_account', 'calendar','microsoft_calendar'],
#
#     'data': [],
#     'demo': [],
#     'installable': True,
#     'auto_install': False,
# }

# -*- coding: utf-8 -*- 
{
    'name': 'Odes Outlook Calendar',
    'category': 'Uncategorized',
'version': '17.0.1.0.0',    'author': "SGEEDE",
    'website': "https://odes.com.sg", 
    'description':
        """
Odes Outlook Calendar Custom.
===========================

        """,
    'depends': ['microsoft_account', 'calendar','microsoft_calendar'],
    'auto_install': False,
    'data': [
        'views/calendar_event_views.xml',
    ],
    'license': 'LGPL-3',
}
