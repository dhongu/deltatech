{
    "images": ["static/description/main_screenshot.png"],
    "name": "Report Packaging",
    "summary": "Report packaging materials used for invoiced products",
    "version": "19.0.1.0.0",
    "category": "Product",
    "author": "Terrabit",
    "website": "https://www.terrabit.ro",
    "license": "LGPL-3",
    "depends": ["account", "product"],
    "data": [
        "security/ir.model.access.csv",
        "views/product_view.xml",
        "views/account_move_view.xml",
        "wizard/invoice_packaging_material_view.xml",
    ],
    "development_status": "Beta",
    "maintainers": ["cojocariudaniel1", "dhongu"],
}
