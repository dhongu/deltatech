{
    "name": "Product Reordering Limit",
    "summary": "Custom reordering limits for products",
    "version": "18.0.1.0.1",
    "author": "Terrabit, Voicu Stefan",
    "website": "https://www.terrabit.ro",
    "category": "Inventory",
    "depends": ["product", "stock"],
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "views/product_template_view.xml",
        "wizard/product_reordering_report_wizard_view.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["VoicuStefan2001"],
}
