{
    "images": ["static/description/main_screenshot.png"],
    "name": "Report Packaging",
    "summary": "Report packaging materials used for invoiced products",
    "version": "20.0.1.3.4",
    "category": "Product",
    "author": "Terrabit",
    "website": "https://www.terrabit.ro",
    "license": "LGPL-3",
    "depends": ["account", "product"],
    "data": [
        "security/ir.access.csv",
        "views/product_view.xml",
        "views/account_move_view.xml",
        "wizard/invoice_packaging_material_view.xml",
    ],
    "development_status": "Beta",
    "maintainers": ["cojocariudaniel1", "dhongu"],
}
