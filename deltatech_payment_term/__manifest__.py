# ©  2018 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Payment Term Rate Wizard",
    "version": "11.0.2.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Generic Modules/Base",
    "depends": ["account", "sale", "deltatech_account"],
    "license": "LGPL-3",
    "data": [
        "wizard/payment_term_view.xml",
        "views/sale_view.xml",
        "views/account_view.xml",
        "views/account_invoice_view.xml",
        "views/res_partner_view.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
