{
    "name": "CRM Contact Enhancement",
    "version": "17.0.1.0.0",
    "category": "Contacts",
    "summary": "Reorder address fields and require Country before State/City/ZIP",
    "description": """
Enhancements for contact address entry:
- Reorder address fields (Country first, then State/City/ZIP, then Street/Street 2)
- Hide State/City/ZIP until Country is selected
- Apply changes to main contact form, child address form, and private address form
""",
    "license": "LGPL-3",
    "depends": ["base", "contacts", "base_address_extended"],
    "data": [
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
}
