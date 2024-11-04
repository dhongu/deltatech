# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Invoice Followup",
    "summary": "Simple invoice followup, with automatic e-mails",
    "version": "18.0.0.0.4",
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
        "security/ir.model.access.csv",
    ],
    "license": "OPL-1",
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Alpha",
}
