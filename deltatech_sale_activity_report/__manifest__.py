{
    "name": "Sale Activity Log",
    "version": "19.0.1.2.2",
    "author": "Terrabit, Voicu Stefan",
    "website": "https://www.terrabit.ro",
    "category": "Sales",
    "summary": "Daily journal of the changes each user makes on sales orders",
    "depends": ["sale", "data_recycle"],
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/sale_activity_record_view.xml",
        "data/recycle_rules.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["VoicuStefan2001"],
}
