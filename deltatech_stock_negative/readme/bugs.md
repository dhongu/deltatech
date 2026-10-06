# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## STOCK-001 — P2: Disabling serial checks blocks available serialized stock

- **Status:** Fixed in 19.0.2.0.11. When the product is serial-tracked and the
  location has Check Serial No. disabled, `_check_no_negative_stock()` no longer
  adds any `lot_id` condition to the quant domain, so the physical quantity is
  summed across all serial numbers (product/location/package/owner filters
  kept); the consumption key uses one aggregate lot slot (`None`) so several
  lines on different serials share that stock. With the serial check enabled the
  check stays per lot. Covered by `tests/test_negative_serial.py` (the two
  "allowed" cases failed before the fix).
- **Priority:** re-evaluated from P1 to P2 on 2026-10-01: `check_serial_no`
  defaults to True, the scenario requires disabling it explicitly, and the effect
  is a blocked validation, not corrupted data.
- **Location:** `models/stock.py`, `_check_no_negative_stock()`, lines 77–82.
- **Trigger:** Enable the company's no-negative-stock policy, disable Check Serial No. on an internal location, and validate an outgoing move for a serialized product stocked on serial-number quants.
- **Actual behavior:** The code clears `lot_id`, then searches explicitly for quants with `lot_id = False`. This excludes the serialized quants rather than aggregating stock across serial numbers.
- **Expected behavior:** With serial checks disabled, the physical-stock check considers the product's available physical quantity across serial numbers while retaining the other location/package/owner filters.
- **Impact:** A legitimate transfer is blocked as negative stock even when sufficient serialized stock exists.
- **Evidence:** Isolated execution reproduced a blocked move for one available serialized unit and captured a quant domain containing `('lot_id', '=', False)`.
- **Suggested fix:** Omit the lot filter when serial checking is disabled, and align the consumption grouping with that aggregation.
- **Validation needed:** Serialized products with serial checking enabled and disabled, including multiple lines consuming the same aggregate stock.

## STOCK-002 — P3: Absent serial passes when Check Serial No. is off

- **Status:** Open — needs a design decision, not a code fix. Found on 2026-10-01 while writing the
  consultant sheet.
- **Location:** `models/stock.py`, `_check_no_negative_stock()`.
- **Trigger:** Location with Check Serial No. disabled, serial SN-1 in stock, a move line on SN-2
  (not in the location).
- **Actual behavior:** The check passes on the location total, and the core then decreases the
  quant of the line's serial: SN-2 ends at -1 while SN-1 stays at +1. The location total is right,
  the per-serial records are not.
- **Expected behavior:** To decide. Disabling the serial check is meant for locations where the
  serial is recorded only at the exit, so passing is the intended effect; the open question is
  whether the module should also move the stock off a present serial, or warn.
- **Coverage:** `tests/test_negative_serial.py::test_serial_check_off_absent_serial_passes_on_the_total`
  pins the current behavior; the consultant sheet documents it (step 7, known limitations).

## Review limitations

Verified against the local Odoo 19 source and, where stated, by isolated execution with mocked ORM objects. No database-backed integration tests were run at review time. STOCK-001 was
later fixed and covered by database-backed tests (2026-10-01).

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **STOCK-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.

## STOCK-003 — P2: No-negative-stock enforcement blocks products whose stock is not tracked

- **Status:** Open; reviewed 2026-10-03.
- **Location:** models/stock.py, StockMoveLine._action_done(), _check_no_negative_stock().
- **Trigger:** Enable the company no-negative-stock policy and deliver a product with type consu and is_storable=False from an internal location that disallows negative stock.
- **Actual behavior:** The addon checks every positive move-line quantity against physical quants without checking product.is_storable. Such a product normally has no quants, so quantity 1 is compared against zero and rejected before native completion.
- **Impact:** Normal deliveries containing products without inventory tracking cannot be validated under the company's stock policy, despite not reducing tracked stock.
- **Evidence:** Traced native stock.move._should_bypass_reservation and stock.move.line._synchronize_quant, which bypass reservations and quant updates for nonstorable products. Executed the actual addon checker with a nonstorable product and an empty quant set: it raised the negative-stock UserError. Reproduction: audit_coverage/reproductions/negative_nonstorable.py. Existing negative-stock tests use storable products. No database picking validation executed.
- **Suggested fix:** Restrict physical-stock enforcement to products whose quantities native stock tracks; preserve all existing location, company, lot/package/owner and batch-consumption behavior.
- **Validation needed:** Mixed storable/nonstorable deliveries, no-negative-stock enabled/disabled, allowed-negative locations and positive/zero quantities. Assert that nonstorable lines do not query or consume physical stock.
