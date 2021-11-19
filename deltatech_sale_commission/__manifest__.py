# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Sale Commission",
    "summary": "Compute sale commission",
    "version": "15.0.1.0.1",
    "category": "Sales",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["deltatech_sale_margin"],
    "license": "LGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "views/account_invoice_view.xml",
        "report/sale_margin_report.xml",
        "views/commission_users_view.xml",
        "wizard/commission_compute_view.xml",
        "wizard/update_purchase_price_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
