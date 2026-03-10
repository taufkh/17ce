{
    "name": "CRM Quotation Tracker",
    "version": "1.2",
    "license": "LGPL-3",
    "summary": "Track quotation lines per CRM opportunity",
    "depends": ["crm", "sales_team", "sale_crm"],
    "data": [
        "security/ir.model.access.csv",
        "security/quotation_tracker_rules.xml",
        "views/quotation_manufacturer_views.xml",
        "views/crm_lead_view.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "crm_quotation_tracker/static/src/scss/quotation_ribbon.scss"
        ]
    },
    "installable": True
}
