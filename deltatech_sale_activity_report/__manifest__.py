{
    "name": "Sale Order Last Modified",
    "version": "18.0.0.0.8",
    "author": "Terrabit, Voicu Stefan",
    "website": "https://www.terrabit.ro",
    "category": "Sales",
    "summary": "Adds a last modified field to the sale order",
    "depends": ["sale", "data_recycle"],
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "views/sale_activity_record_view.xml",
        "data/recycle_rules.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["VoicuStefan2001"],
}
