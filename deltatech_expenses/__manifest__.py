# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Expenses Deduction",
    "summary": "Expenses Deduction & Disposition of Cashing",
    "version": "19.0.3.1.0",
    "category": "Accounting & Finance",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": [
        "l10n_ro",
        "account",
        "product",
        "hr",
        "hr_expense",
        "deltatech_partner_generic",
        # "deltatech_payment_to_statement",
    ],
    "license": "OPL-1",
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/deltatech_expenses_deduction_view.xml",
        "views/deltatech_expenses_deduction_report.xml",
        "views/report_expenses.xml",
        "views/account_journal_view.xml",
        "views/hr_expense_view.xml",
        "views/hr_employee_view.xml",
        "wizard/expenses_import_hr_view.xml",
        "data/data.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
