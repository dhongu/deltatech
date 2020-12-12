# ©  2008-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Invoice Number",
    "summary": "Renumbering invoice",
    "version": "14.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Accounting",
    "depends": ["account"],
    "license": "LGPL-3",
    "data": [
        "security/sale_security.xml",
        # "views/account_invoice_view.xml",
        "wizard/account_invoice_change_number_view.xml",
        "security/ir.model.access.csv",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
