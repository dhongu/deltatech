# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Payment Report",
    "version": "20.0.1.0.4",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "summary": "Payment analysis report by journal and period, with a filter wizard",
    "category": "Generic Modules",
    "depends": ["account"],
    "license": "OPL-1",
    "data": [
        "wizard/payment_report_view.xml",
        "security/ir.access.csv",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
