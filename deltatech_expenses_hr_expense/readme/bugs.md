# Known bugs

Review date: 2026-10-08. Target version: Odoo 19.

## EXPHR-001 — P3: Interface texts are written in Romanian in the source

- **Status:** Open on 19.0.
- **Location:** `views/deltatech_expenses_deduction_view.xml`, line 11; `wizard/expenses_import_hr_view.xml`, lines 7, 9, 12, 31, 32, 40; `models/deltatech_expenses_deduction.py`, lines 41, 53, 83, 86, 110; `models/hr_expense.py`, line 20; `wizard/expenses_import_hr.py`, lines 38, 46.
- **Trigger:** A user whose language is not Romanian opens an expense report or the "Add to expense report" action.
- **Actual behavior / impact:** The button "Preia cheltuieli HR", the wizard ("Angajat", "Decont de cheltuieli", "Preia", "Renunță"), the server action "Adaugă în decont de cheltuieli", the error messages and two field helps are shown in Romanian to every user. Odoo expects English source terms translated through `i18n/ro.po`; the module has no `i18n` folder, so the texts cannot be translated either.
- **Evidence:** Source inspection; the Apps page and the screenshots are in English, the interface is not.
- **Suggested fix:** Write the source terms in English (for example "Get HR Expenses", "Employee", "Expense Report", "Get", "Cancel", "Add to Expense Report"), then generate `i18n/deltatech_expenses_hr_expense.pot` and put the current Romanian texts in `i18n/ro.po`.
- **Validation needed:** With the user in English the texts are English; with the user in Romanian they are unchanged.
- **Limitations:** Translation only; no change in behavior.
