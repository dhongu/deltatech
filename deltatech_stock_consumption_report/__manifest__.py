# © 2026 Terrabit
# See README.rst file on addons root folder for license details
{
    "name": "Stock Consumption Report",
    "summary": "Monthly report of the consumption vouchers by store and purpose, with XLSX export",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "category": "Inventory/Inventory",
    "depends": [
        "stock_account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/consumption_purpose_views.xml",
        "views/stock_picking_views.xml",
        "wizard/consumption_report_wizard_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
