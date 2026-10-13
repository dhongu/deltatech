# Confirmed bugs — 2026-10-03

## INVWEIGHT-001 — P2: quantities are not normalized to product unit

Invoice, sale and purchase create overrides multiply product.weight and l10n_ro_net_weight by raw line quantity. That quantity is expressed in invoice product_uom_id, sale product_uom_id or purchase product_uom_id, while weight is per product base unit. One dozen of a product weighing 2 kg per unit yields 2 instead of 24. Convert the quantity to product.uom_id before multiplying in all three paths.

Evidence: full source and native stock.move product_qty UoM conversion contract read, native purchase product_qty field is raw ordered quantity. Source/arithmetic proof; no database documents created.

## INVWEIGHT-002 — P2: kilogram fields directly receive pounds

Gross-weight fields promise kg in help text but copy product.weight directly. Native product.weight_in_lbs=1 interprets product weight in pounds. One product of weight 10 lb yields gross weight 10 in a field documented as kg rather than about 4.536 kg. Convert configured product weight into kg, or display and document the configured unit consistently. Net-weight custom field has no explicit unit, so its pounds semantics are not asserted.

Evidence: native product weight configuration helper read; source/arithmetic proof only, no configured database/report test.

## Limits

Full source and native view/report anchors checked. Fields are manual snapshots assigned only at create; later line edits do not refresh, and explicit initial manual weights are overwritten. These behavior/persistence choices require policy validation before separate findings. Package weight is not included in totals; no package aggregation requirement inferred. No database/report/browser tests executed.
