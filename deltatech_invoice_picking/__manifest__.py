# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Invoice Pickings",
    "version": "14.0.1.0.3",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "summary": "Facturare livrari",
    "category": "Sales",
    "depends": ["base", "sale_management", "stock", "sale_stock", "stock_picking_batch", "purchase"],
    "price": 5.00,
    "currency": "EUR",
    "license": "LGPL-3",
    "data": [
        "views/stock_view.xml",
        "views/sale_view.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
