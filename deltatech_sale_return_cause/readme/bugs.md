# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## RETURNCAUSE-001 — P2: Bulk return-cause updates fail on singleton field reads

- **Status:** Open.
- **Location:** models/sale_order.py, write(), lines 38–43, and check_and_update_return_amount(), lines 67–76.
- **Trigger:** Write a nonempty return_cause or return_cause_id on a recordset containing multiple sale orders, or call check_and_update_return_amount() on that recordset.
- **Actual behavior:** write reads the scalar Date field self.return_cause_date on multiple records. The amount updater loops over order but reads scalar fields and invoice_ids from self rather than order. Odoo scalar field access requires a singleton and raises Expected singleton.
- **Evidence:** Source inspection of both methods and the ORM scalar-field contract. The cron calls the updater one order at a time, so that path does not exercise the defect. No database reproduction was run.
- **Impact:** Batch changes through ORM/RPC or server actions fail; batch recalculation cannot process individual orders correctly.
- **Suggested fix:** Handle each order individually where existing dates differ, preserve explicitly supplied dates, and use order fields inside the amount-update loop.
- **Validation needed:** Bulk writes with unset and existing dates, explicit date overrides, and a multi-order recalculation with distinct credit notes.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
