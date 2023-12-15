# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Invoice Delivery / Reception",
    "summary": "Adding button in invoice for display reception or delivery",
    "version": "17.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "category": "Generic Modules/Other",
    "depends": [
        "account",
        "stock",
        "purchase",
        "sale",
        #    "deltatech_account",  # pentru adaugare grup de butoane
    ],
    "data": ["views/account_invoice_view.xml"],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
