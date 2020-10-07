# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Sale Margin",
    "version": "12.0.1.0.0",
    "category": "Sales",
    "author": "Terrabit, Dorin Hongu",
    "website": "",
    "depends": ["sale_margin", "account"],
    "license": "LGPL-3",
    "data": [
        "security/sale_security.xml",
        "security/ir.model.access.csv",
        "views/sale_margin_view.xml",
        "views/account_invoice_view.xml",
        "report/sale_margin_report.xml",
        "views/commission_users_view.xml",
        "wizard/commission_compute_view.xml",
        "wizard/update_purchase_price_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "stable",
    "maintainers": ["dhongu"],
}
