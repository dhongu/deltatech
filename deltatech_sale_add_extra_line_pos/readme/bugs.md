# Confirmed bugs — 2026-10-03

## POSEXTRA-001 — P2: cancelled main-product addition still adds extra

The addLineToCurrentOrder patch awaits super but never checks the returned line. Native addLineToOrder returns undefined when configuration/combo/lot entry is cancelled or refund constraints reject addition. The patch still examines vals and adds its configured extra product to the order. Cancel a configurable product with an extra: the main line is absent but the extra is added and charged. Exit when super did not add a line.

Evidence: complete addon JS and native pos_store.js:887–1025 early-return paths read. Source-only, no popup/browser test executed.

## POSEXTRA-002 — P2: deleting a main line leaves extra quantity unchanged

Only addition and PosOrderline.setQuantity are patched. Native PosOrder.removeOrderline (:419–435) calls line.delete directly, without setQuantity. Removing a main product therefore leaves the consolidated extra quantity based on the deleted demand until another relevant update occurs. Synchronize after removal and drop zero-demand generated extras while preserving manual lines according to policy.

Evidence: addon hooks and native removal flow read; no browser deletion test executed.

## POSEXTRA-003 — P2: first extra uses input quantity instead of actual accepted quantity

When no extra line exists, the patch computes qty from vals.qty || 1. Native addLineToOrder can derive a different quantity, including weighed quantity from the scale and negative default for return presets. First add a weighed main product of 2.5 units with no vals.qty and extra_qty 1: generated extra is 1 instead of 2.5. A return preset similarly defaults main quantity to -1 while the extra request is explicitly +1, subject to refund guards. Use actual resulting order demand/line quantity for generation and reconcile after creation. Subsequent updates use aggregate line.qty, so this specifically affects first creation.

Evidence: native values default and scale values.qty assignment traced; no scale/return/browser test executed. Refund constraints may reject the incorrect positive extra rather than persist it.

## Limits

Loader fields, imported Odoo 19 classes and template/variant resolution checked. extra_percent is loaded but unused in POS; documented feature scope emphasizes quantity, so no separate percentage-pricing defect asserted. Self/cyclic product configuration can cause setQuantity recursion; production data/configuration policy not runtime-tested. No JS fixture or browser/database execution in this round.
