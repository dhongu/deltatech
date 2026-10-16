# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Invoice Pickings",
    "version": "20.0.1.0.15",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "live_test_url": "https://www.terrabit.ro/demo/deltatech_invoice_picking?v=20.0",
    "support": "support@terrabit.ro",
    "summary": "Create invoices directly from stock pickings or batch transfers",
    "category": "Sales",
    "depends": ["account", "sale_management", "stock", "sale_stock", "purchase", "purchase_stock"],
    "price": 5.00,
    "currency": "EUR",
    "license": "LGPL-3",
    "data": [
        "views/stock_view.xml",
        "views/sale_view.xml",
        "views/account_move.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
