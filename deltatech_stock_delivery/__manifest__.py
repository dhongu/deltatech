# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Invoice Delivery / Reception",
    "summary": "Adding button in invoice for display reception or delivery",
    "version": "13.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "LGPL-3",
    "category": "Generic Modules/Other",
    "depends": [
        "account",
        "stock",
        #    "deltatech_account",  # pentru adaugare grup de butoane
    ],
    "data": ["views/account_invoice_view.xml"],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
