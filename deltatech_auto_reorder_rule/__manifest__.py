# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Auto Reorder Rule",
    "category": "Stock",
    "summary": "Auto create reorder rule",
    "version": "17.0.0.1.2",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "depends": ["stock", "purchase_stock", "sale_stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_server_action.xml",
        "views/stock_warehouse_view.xml",
        "views/stock_route_view.xml",
        "wizard/order_rules_details_view.xml",
    ],
    "development_status": "Beta",
    "installable": True,
}
