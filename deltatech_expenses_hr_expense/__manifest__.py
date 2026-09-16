# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details


{
    "images": ["static/description/main_screenshot.png"],
    "name": "Expenses Deduction - HR Expense Bridge",
    "summary": "Preia cheltuielile standard (hr_expense) în Decontul de cheltuieli (deltatech_expenses)",
    "version": "19.0.1.0.0",
    "category": "Accounting & Finance",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": [
        "deltatech_expenses",
        "hr_expense",
    ],
    "auto_install": True,
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "views/deltatech_expenses_deduction_view.xml",
        "views/hr_expense_view.xml",
        "wizard/expenses_import_hr_view.xml",
    ],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
