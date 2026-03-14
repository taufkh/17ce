# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Newsletter Subscribe Button',
    'summary': 'Attract visitors to subscribe to mailing lists',
    'description': """
This module brings a new building block with a mailing list widget to drop on any page of your website.
On a simple click, your visitors can subscribe to mailing lists managed in the Email Marketing app.
    """,
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'category': 'Website/Website',
    'depends': ['website', 'mass_mailing'],
    'data': [
        'security/ir.model.access.csv',
        'views/website_mass_mailing_templates.xml',
        'views/snippets_templates.xml',
        'views/mailing_list_views.xml',
        'views/website_mass_mailing_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_mass_mailing/static/src/scss/website_mass_mailing_popup.scss',
            'website_mass_mailing/static/src/js/website_mass_mailing.js',
        ],
        'web.assets_wysiwyg': [
            'website_mass_mailing/static/src/js/website_mass_mailing.editor.js',
        ],
    },
    'auto_install': True,
}
