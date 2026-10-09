# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Product Secondary UoM",
    "version": "20.0.1.2.1",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "summary": "Product specific conversion factors between units of measure (SAP MARM style)",
    "category": "Inventory/Inventory",
    "depends": [
        "sale_stock",
        "purchase_stock",
    ],
    "data": [
        "security/ir.access.csv",
        "views/product_template_views.xml",
        "views/sale_order_views.xml",
        "views/purchase_order_views.xml",
        "views/stock_picking_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
