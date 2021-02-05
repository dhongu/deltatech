# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Expenses Deduction",
    "summary": "Expenses Deduction & Disposition of Cashing",
    "version": "14.0.1.0.2",
    "category": "Accounting & Finance",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["account", "product", "deltatech_partner_generic"],
    "license": "LGPL-3",
    "data": [
        "views/deltatech_expenses_deduction_view.xml",
        "views/deltatech_expenses_deduction_report.xml",
        "views/report_expenses.xml",
        "views/account_journal_view.xml",
        "security/ir.model.access.csv",
        "data/data.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
