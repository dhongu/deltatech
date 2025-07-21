{
    "name": "Create excel with a pricelist",
    "version": "17.0.0.0.1",
    "author": "Voicu Stefan, Terrabit",
    "website": "https://www.terrabit.ro",
    "summary": "Let's you generate an excel with all products based on a pricelist",
    "category": "Sales",
    "depends": ["sale_management", "product"],
    "data": [
        "security/ir.model.access.csv",
        # "data/server_action.xml",
        "wizard/pricelist_excel_wizard_view.xml",
    ],
    "license": "OPL-1",
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Alpha",
    "maintainers": ["VoicuStefan2001"],
}
