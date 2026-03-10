{
    "name": "CRM Base Address Extended",
    "version": "17.0.1.0.0",
    "category": "Contacts",
    "summary": "On-demand city import with state-based city selection",
    "license": "LGPL-3",
    "depends": ["contacts", "base_address_extended", "crm_contact_enhancement"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "wizard/city_import_wizard_view.xml",
        "wizard/state_import_wizard_view.xml",
    ],
    "installable": True,
    "application": False,
    "description": """
Adds on-demand city import and state-based city selection for contacts.

Data source (ODbL-1.0): https://github.com/dr5hn/countries-states-cities-database
""",
}
