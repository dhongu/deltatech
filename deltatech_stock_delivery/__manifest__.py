# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Invoice Delivery / Reception",
    "version": "12.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "license": "LGPL-3",
    "category": "Generic Modules/Other",
    "depends": [
        "account",
        "stock",
        "deltatech_account",  # pentru adaugare grup de butoane
        # "l10n_ro_stock_account",
        # 'stock_picking_invoice_link'
    ],
    "data": ["views/account_invoice_view.xml"],
    "images": ["images/main_screenshot.png"],
    "development_status": "stable",
    "maintainers": ["dhongu"],
}
