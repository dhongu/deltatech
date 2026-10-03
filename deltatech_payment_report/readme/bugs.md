# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## PAYREPORT-001 — P1: The report excludes every valid Odoo 19 payment state

- **Status:** Fixed in 19.0.1.0.3 — `do_compute()` filters on the Odoo 19 states `in_process` and `paid` instead of the removed `posted`/`reconciled`; draft, canceled and rejected receipts stay excluded. Covered by tests in `tests/test_payment_report.py` (one receipt in each of the five states, only in_process and paid are reported).
- **Location:** `wizard/payment_report.py:26–37, do_compute()`.
- **Trigger:** Register customer receipts in states in_process or paid and open Payment Report for their dates and journals.
- **Actual behavior / impact:** The search accepts only posted and reconciled, neither of which is an account.payment state in the local Odoo 19 account module. Valid receipts are excluded and the report is empty.
- **Evidence:** Compared the core selection draft/in_process/paid/canceled/rejected. Executed the extracted method against mock payments in paid and in_process: zero report lines were created.
- **Suggested fix:** Use the current payment states according to the intended inclusion policy, excluding draft/canceled/rejected.
- **Validation needed:** Create valid receipts in both current states plus draft and canceled receipts and assert the report includes only the intended posted receipts.
- **Limitations:** Source comparison and extracted-method checks with mocked records; no database-backed integration tests were executed.

## PAYREPORT-002 — P2: PDF printing invokes report_action on a window action

- **Status:** Open. Identified on 2026-10-02.
- **Location:** `wizard/payment_report.py:71–73, print_pdf(); wizard/payment_report_view.xml:105`.
- **Trigger:** Invoke the wizard print_pdf method, advertised by PaymentReportLine.get_general_buttons() as Print Preview.
- **Actual behavior / impact:** The XML ID action_account_payment_report_line resolves to ir.actions.act_window, but print_pdf calls report_action on it. Window actions have no such method. The module manifest also declares no PDF report action/template, so printing raises AttributeError.
- **Evidence:** Verified the XML action model and manifest; extracted-method execution with a window action raised AttributeError for report_action. The standard Show action uses the same XML ID correctly as a window action.
- **Suggested fix:** Define and reference an ir.actions.report and its template, or remove the unsupported preview helper until a report is implemented.
- **Validation needed:** Invoke printing against a real report action and validate PDF contents; keep the standard Show behavior working.
- **Limitations:** Source comparison and extracted-method checks with mocked records; no database-backed integration tests were executed.
