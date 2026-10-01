# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## STOCK-001 — P1: Disabling serial checks blocks available serialized stock

- **Status:** Open.
- **Location:** `models/stock.py`, `_check_no_negative_stock()`, lines 77–82.
- **Trigger:** Enable the company's no-negative-stock policy, disable Check Serial No. on an internal location, and validate an outgoing move for a serialized product stocked on serial-number quants.
- **Actual behavior:** The code clears `lot_id`, then searches explicitly for quants with `lot_id = False`. This excludes the serialized quants rather than aggregating stock across serial numbers.
- **Expected behavior:** With serial checks disabled, the physical-stock check considers the product's available physical quantity across serial numbers while retaining the other location/package/owner filters.
- **Impact:** A legitimate transfer is blocked as negative stock even when sufficient serialized stock exists.
- **Evidence:** Isolated execution reproduced a blocked move for one available serialized unit and captured a quant domain containing `('lot_id', '=', False)`.
- **Suggested fix:** Omit the lot filter when serial checking is disabled, and align the consumption grouping with that aggregation.
- **Validation needed:** Serialized products with serial checking enabled and disabled, including multiple lines consuming the same aggregate stock.

## Review limitations

Verified against the local Odoo 19 source and, where stated, by isolated execution with mocked ORM objects. No database-backed integration tests were run. No fixes have been applied.
