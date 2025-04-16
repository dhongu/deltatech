# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Stock Inventory Product Display",
    "summary": "Adds product display button on sales and invoices to see the stock of the products in the order",
    "version": "18.0.0.0.0",
    "author": "Terrabit, VoicuStefan2001",
    "website": "https://www.terrabit.ro",
    "category": "Warehouse",
    "depends": [
        "deltatech_stock_inventory",
        "sale",
    ],
    "license": "OPL-1",
    "data": [
        "views/account_move_view.xml",
        "views/sale_order_view.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Production/Stable",
    "maintainers": ["VoicuStefan2001"],
}
