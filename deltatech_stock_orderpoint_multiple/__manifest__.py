# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

{
    "images": ["static/description/main_screenshot.png"],
    "name": "Stock Orderpoint Qty Multiple",
    "summary": "Restore the 'Multiple Quantity' rounding on reordering rules removed in Odoo 19",
    "version": "19.0.1.0.0",
    "author": "Terrabit",
    "website": "https://www.terrabit.ro",
    "category": "Inventory",
    "license": "LGPL-3",
    "depends": ["stock"],
    "data": [
        "views/stock_warehouse_orderpoint_views.xml",
    ],
    "development_status": "Beta",
    "maintainers": ["VoicuStefan2001"],
}
