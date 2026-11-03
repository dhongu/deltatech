# © 2025 Deltatech
# See README.rst file on addons root folder for license details

{
    "images": ["static/description/main_screenshot.png"],
    "name": "Purchase Orders Bulk Email with XLSX",
    "summary": "Send several purchase orders of the same vendor in one email, with an XLSX summary and the PDFs",
    "version": "19.0.1.1.6",
    "author": "Deltatech, Terrabit",
    "license": "LGPL-3",
    "category": "Purchases",
    "website": "https://www.terrabit.ro",
    "depends": ["purchase", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_template.xml",
        "views/purchase_order_actions.xml",
    ],
    "development_status": "Production/Stable",
}
