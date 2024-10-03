# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Invoice Report",
    "summary": "Invoice Report",
    "version": "15.0.1.0.7",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "category": "Accounting",
    "depends": ["account", "product"],
    "data": [
        "security/ir.model.access.csv",
        "report/invoice_report_view.xml",
        "views/product_view.xml",
        "data/ir_cron_data.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
