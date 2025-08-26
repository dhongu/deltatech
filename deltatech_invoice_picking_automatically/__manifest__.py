# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Invoice Pickings Automatically",
    "version": "17.0.0.0.1",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "summary": "Generate invoice automatically from picking after validation",
    "category": "Sales",
    "depends": ["sale_stock"],
    "price": 5.00,
    "currency": "EUR",
    "license": "LGPL-3",
    "data": ["views/stock_picking_view.xml"],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
