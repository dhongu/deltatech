# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Stock Date",
    "summary": "Set posting date for stock move",
    "version": "16.0.1.0.8",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Warehouse",
    "depends": ["base", "stock_account", "purchase_stock"],
    "license": "OPL-1",
    "data": [
        "wizard/stock_immediate_transfer_view.xml",
        "wizard/stock_backorder_confirmation_view.xml",
        "wizard/stock_picking_return_view.xml",
        "data/ir_config_parameter.xml",
        # "views/stock_picking.xml",
    ],
    "application": False,
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
