{
    "name": "CRM Project Classification",
    "version": "1.0",
    "license": "LGPL-3",
    "summary": "Adds category-dependent project status in CRM",
    "depends": ["crm", "crm_timeline_engagement"],
    "data": [
        "security/ir.model.access.csv",
        "data/project_classification_data.xml",
        "views/crm_lead_view.xml"
    ],
    "installable": True
}
