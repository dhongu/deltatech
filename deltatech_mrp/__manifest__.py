# ©  2008-2019 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "MRP Extension",
    "summary": "Cost categories for components and a production cost analysis for manufacturing orders",
    "version": "20.0.1.0.10",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "category": "Generic Modules/Production",
    "depends": ["base", "mrp", "stock", "stock_account", "sale", "product"],
    "data": [
        "views/mrp_view.xml",
        "report/deltatech_mrp_report.xml",
        "views/product_view.xml",
        "security/ir.access.csv",
    ],
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
