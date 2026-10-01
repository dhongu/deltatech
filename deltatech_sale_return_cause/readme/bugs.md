# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## RETURNCAUSE-001 — P2: Bulk return-cause updates fail on singleton field reads

- **Status:** Fixed on 2026-10-01 in 19.0.0.0.10. write() fills return_cause_date with today only on the orders that have no date (the existing dates are kept) and only when return_cause_date is not in vals, so an explicitly supplied date is no longer replaced; check_and_update_return_amount() reads return_cause, return_cause_id, invoice_count and invoice_ids from each order. Covered by tests 05–07; the test setup no longer uses is_storable, which needs stock (not a dependency), so the module tests now run on a sale-only install.
- **Location:** models/sale_order.py, write(), lines 38–43, and check_and_update_return_amount(), lines 67–76.
- **Trigger:** Write a nonempty return_cause or return_cause_id on a recordset containing multiple sale orders, or call check_and_update_return_amount() on that recordset.
- **Actual behavior:** write reads the scalar Date field self.return_cause_date on multiple records. The amount updater loops over order but reads scalar fields and invoice_ids from self rather than order. Odoo scalar field access requires a singleton and raises Expected singleton.
- **Evidence:** Source inspection of both methods and the ORM scalar-field contract. The cron calls the updater one order at a time, so that path does not exercise the defect. No database reproduction was run.
- **Impact:** Batch changes through ORM/RPC or server actions fail; batch recalculation cannot process individual orders correctly.
- **Suggested fix:** Handle each order individually where existing dates differ, preserve explicitly supplied dates, and use order fields inside the amount-update loop.
- **Additional finding (2026-10-01 verification):** on a single order without a stored date, a return_cause_date passed explicitly together with the cause was overwritten with today's date.
- **Validation needed:** Bulk writes with unset and existing dates, explicit date overrides, and a multi-order recalculation with distinct credit notes. Done in tests 05, 06 and 07.

## Review limitations

The initial review was based on source inspection only. The fix was validated with the module tests on a database with only this module installed (7 tests, 0 failures).
