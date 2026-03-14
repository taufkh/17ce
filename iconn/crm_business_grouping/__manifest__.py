{
    "name": "CRM Business Grouping",
    "version": "1.1",
    "license": "LGPL-3",
    "summary": "Business Grouping master data for CRM opportunities",
    "depends": ["crm"],
    "data": [
        "security/ir.model.access.csv",
        "data/business_grouping_data.xml",
        "views/business_grouping_views.xml",
        "views/crm_lead_view.xml"
    ],
    "installable": True
}
