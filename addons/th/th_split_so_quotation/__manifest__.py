{
    "name": "Split / Extract Quotation",
    "version": "1.0",
    "summary": "Split or extract quotation lines into new quotations",
    "depends": ["sale"],
    "data": [
        "security/split_extract_security.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings_view.xml",
        "views/sale_order_view.xml",
        "views/sale_order_split_wizard.xml"
    ],
    "installable": True
}
