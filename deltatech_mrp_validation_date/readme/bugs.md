# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## MRPDATE-001 — P2: Validation date is populated before manufacturing completion

- **Status:** Open. Identified on 2026-10-02.
- **Location:** `models/mrp_order.py:12–15, button_mark_done()`.
- **Trigger:** Click Mark as Done when core MRP opens a pre-completion wizard, then close or cancel that wizard.
- **Actual behavior / impact:** The override sets validation_date unconditionally after the parent call. Core button_mark_done can return a wizard before completing the order. An unfinished production therefore receives a completion date; date.today also follows server date rather than the user context.
- **Evidence:** Verified the early return after pre_button_mark_done in the local core. Executed the extracted override with a wizard action response: validation_date was set while state remained progress.
- **Suggested fix:** Write the date only for records actually transitioned to done, using fields.Date.context_today; preserve dates for already completed records.
- **Validation needed:** Trigger and cancel a pre-completion wizard and verify no validation date; complete the flow and verify the date appears only on done orders.
- **Limitations:** Source comparison and isolated executions of extracted current methods with mocked records; no database-backed integration tests were executed.
