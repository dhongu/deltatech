# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Stock Inventory",
    "summary": "Inventory Old Method",
    "version": "15.0.2.2.2",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Warehouse",
    "depends": ["deltatech_stock_date", "stock", "stock_account"],
    "license": "LGPL-3",
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/stock_inventory_views.xml",
        "views/product_view.xml",
        "views/stock_quant_view.xml",
        "views/report_stockinventory.xml",
        # "views/stock_requests_count_view.xml",
        "wizard/stock_confirm_inventory_view.xml",
        # "wizard/stock_change_product_qty_view.xml",
        "wizard/stock_inventory_merge.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
