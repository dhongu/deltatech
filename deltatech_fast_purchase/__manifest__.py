# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Fast Purchase",
    "version": "20.0.1.0.1",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "live_test_url": "https://www.terrabit.ro/demo/deltatech_fast_purchase?v=20.0",
    "summary": "Confirm, receive and bill a purchase order in one click",
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
