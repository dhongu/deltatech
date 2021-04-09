# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Invoice Followup",
    "summary": "Simple invoice followup, with automatic e-mails",
    "version": "13.0.0.0.1",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "support": "odoo@terrabit.ro",
    "category": "Accounting",
    "external_dependencies": {
        "python": [],
    },
    "depends": [
        "account",
    ],
    "data": [
        "views/res_partner.xml",
        "views/invoice_followup.xml",
        "data/security.xml",
    ],
    "license": "LGPL-3",
    "images": ["static/description/icon.png"],
    "development_status": "Alpha",
}
