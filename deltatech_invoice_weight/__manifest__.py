# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Invoice Weight",
    "summary": "Invoice Weight",
    "version": "18.0.1.0.2",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "category": "Accounting",
    "depends": ["account", "purchase", "stock", "sale"],
    "data": [
        "views/account_invoice_view.xml",
        "views/purchase_order_view.xml",
        "views/sale_order_view.xml",
        "views/invoice_report.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
