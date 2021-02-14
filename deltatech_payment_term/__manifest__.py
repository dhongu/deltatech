# ©  2018 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Payment Term Rate Wizard",
    "summary": "Term Rate Wizard",
    "version": "14.0.2.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Generic Modules/Base",
    "depends": ["account", "sale"],
    "license": "LGPL-3",
    "data": [
        "wizard/payment_term_view.xml",
        "views/sale_view.xml",
        "views/account_view.xml",
        "views/account_invoice_view.xml",
        "views/res_partner_view.xml",
        "security/ir.model.access.csv",
    ],
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
