# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Stock Inventory",
    "summary": "Inventory Old Method",
    "version": "15.0.2.0.3",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Warehouse",
    "depends": ["deltatech_stock_date", "stock_account"],
    "license": "LGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/stock_inventory_views.xml",
        "views/product_view.xml",
        "views/report_stockinventory.xml",
        "views/stock_requests_count_view.xml",
        # "wizard/stock_change_product_qty_view.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
