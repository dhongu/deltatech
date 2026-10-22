# © 2025 Deltatech
# See README.rst file on addons root folder for license details

{
    "images": ["static/description/main_screenshot.png"],
    "name": "Purchase Orders Bulk Email with XLSX",
    "summary": "Select multiple purchase orders and send an email with XLSX summary and attached PDFs",
    "version": "19.0.1.1.5",
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
