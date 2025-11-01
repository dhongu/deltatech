# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Fast Purchase",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "summary": "Achizitie rapida",
    "category": "Purchases",
    "depends": ["base", "purchase_stock", "stock"],
    "license": "OPL-1",
    "support": "odoo@terrabit.ro",
    "data": ["views/purchase_view.xml", "views/stock_view.xml"],
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
    "price": 5.00,
    "currency": "EUR",
}
