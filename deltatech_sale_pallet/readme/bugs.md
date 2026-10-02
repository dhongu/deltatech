# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## PALLET-001 — P2: Pallet rounding is incorrect near integer boundaries

- **Status:** Fixed in 19.0.1.0.11. `compute_pallet_number()` now uses
  `math.floor` / `math.ceil` with a tolerance of half the `Product Unit`
  precision, expressed in pallets. Covered by
  `test_compute_pallet_number_boundaries` (exact multiples, just below, just
  above, fractional quantities).
- **Location:** `models/sale.py`, `compute_pallet_number()`.
- **Trigger:** Use fractional product quantities near a multiple of `pallet_qty_min`.
- **Actual behavior:** `round(pallets - 0.49)` and `round(pallets + 0.49)` approximate floor/ceiling but produce incorrect values near integer boundaries.
- **Examples reproduced:** With 100 units per pallet, 199.5 units yield 2 pallets in round-down mode instead of 1; 100.5 units yield 1 pallet in round-up mode instead of 2.
- **Expected behavior:** Round-down and round-up modes follow their declared direction, with a defined tolerance based on the product unit of measure.
- **Impact:** Orders can contain an incorrect pallet quantity, affecting pallet charges and logistics.
- **Evidence:** Isolated execution of the existing method reproduced both examples.
- **Suggested fix:** Use explicit floor/ceiling logic with a suitable unit-of-measure tolerance.
- **Validation needed:** Values exactly on, just below, and just above pallet multiples, including fractional quantities.

## Review limitations

Verified against the local Odoo 19 source and, where stated, by isolated execution with mocked ORM objects. No database-backed integration tests were run. PALLET-001 was later fixed and covered by a database-backed test.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **PALLET-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.
