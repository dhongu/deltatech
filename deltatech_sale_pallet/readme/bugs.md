# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## PALLET-001 — P2: Pallet rounding is incorrect near integer boundaries

- **Status:** Open.
- **Location:** `models/sale.py`, `compute_pallet_number()`, lines 69–71.
- **Trigger:** Use fractional product quantities near a multiple of `pallet_qty_min`.
- **Actual behavior:** `round(pallets - 0.49)` and `round(pallets + 0.49)` approximate floor/ceiling but produce incorrect values near integer boundaries.
- **Examples reproduced:** With 100 units per pallet, 199.5 units yield 2 pallets in round-down mode instead of 1; 100.5 units yield 1 pallet in round-up mode instead of 2.
- **Expected behavior:** Round-down and round-up modes follow their declared direction, with a defined tolerance based on the product unit of measure.
- **Impact:** Orders can contain an incorrect pallet quantity, affecting pallet charges and logistics.
- **Evidence:** Isolated execution of the existing method reproduced both examples.
- **Suggested fix:** Use explicit floor/ceiling logic with a suitable unit-of-measure tolerance.
- **Validation needed:** Values exactly on, just below, and just above pallet multiples, including fractional quantities.

## Review limitations

Verified against the local Odoo 19 source and, where stated, by isolated execution with mocked ORM objects. No database-backed integration tests were run. No fixes have been applied.
