# © 2025 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Purchase: Send Multi Orders by Email with XLSX",
    "summary": "Select multiple purchase orders and send an email with XLSX summary and attached PDFs",
    "version": "17.0.1.1.1",
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
    "development_status": "Beta",
    "images": ["static/description/main_screenshot.png"],
}
