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

## Integrated review — 2026-10-03

PALLET-001 source rounding fix remains; historical tests not rerun. Full eligible source including unimported sale_report.py read. That report override is inactive in models/__init__.py and is not reported as a runtime failure. Native report action/fields and product/account view anchors exist.

### PALLET-002 — P2: order-line onchange conflicts with extra-product addon

Same confirmed cross-module defect as SALEEXTRA-002: both modules define onchange_order_line without super(). Native callback enumeration registers the final effective method, so the form cannot execute both generators. See deltatech_sale_add_extra_line/readme/bugs.md for evidence and scope.

### PALLET-003 — P2: deleting the last main product leaves its pallet charge

recompute_pallet_lines builds keys only from current lines with pallet configuration. The onchange only updates pallet lines for keys present in that dictionary; it never removes or zeros an existing pallet line for a key that disappeared. Add a main product producing one pallet line, then remove the last main product. The dictionary is empty and the generated pallet line remains in the quotation, still chargeable/deliverable. Track generated pallet ownership and reconcile obsolete lines when main demand disappears; preserve explicitly manual pallet lines according to a clear policy.

Evidence: entire generation/reconciliation loop read; dictionary and unchanged-line branch traced. Source-only, no live-form/database scenario executed. The nonzero dictionary case reducing quantity below minimum does assign zero; this finding specifically concerns disappearance of the last source key.

### PALLET-004 — P2: pallet price cache has no dependencies

pallet_price is nonstored compute but its method has only @api.onchange, not @api.depends. Once read, changes to template.list_price, pallet_qty_min, pallet_product_id or pallet_product_id.list_price do not invalidate the field through ORM dependency triggers. Form onchange covers two local fields but not price changes, imports/RPC or the related pallet product price. Add complete compute dependencies. Native fields.get_depends and models.modified cache invalidation traced. Source evidence only; cache transaction not database-tested.

### Limits

Pallet threshold vs line UoM, manually added duplicate pallet products and inactive report coefficient require broader business-policy/runtime validation. No database/browser/report tests executed.
