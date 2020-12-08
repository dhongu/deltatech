# ©  2008-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Stock Serial Number",
    "summary": "Hide Used Serial Number",
    "version": "13.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Generic Modules/Stock",
    "depends": ["deltatech", "stock", "account", "l10n_ro_stock_picking_report"],
    "images": ["images/main_screenshot.png"],
    "license": "LGPL-3",
    "data": [
        "views/stock_view.xml",
        "views/stock_picking_report_view.xml",
        "views/account_invoice_report_view.xml",
        "views/product_view.xml",
    ],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
