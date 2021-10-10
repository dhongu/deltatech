# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

#     In versiunea 10.0 era si
#     Afisare valoare de vanzare in rapotul de pozitii de stoc (evaluare inventar) si stoc la data

{
    "name": "Stock Inventory",
    "summary": "Inventory enhancements",
    "version": "14.0.2.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Warehouse",
    "depends": ["deltatech_stock_date", "stock_account"],
    "license": "LGPL-3",
    "data": [
        "data/data.xml",
        "views/stock_view.xml",
        "views/product_view.xml",
        "views/report_stockinventory.xml",
        "wizard/stock_change_product_qty_view.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
