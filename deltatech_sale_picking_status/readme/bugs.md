# Confirmed bugs — 2026-10-03

## SALEPICKSTATUS-001 — P2: stored status survives reset to quotation

`models/sale_order.py:10–20` declares an ordinary stored field, without compute/dependencies. Its calculation is called only by picking hooks. Native sale.order.action_draft (:1060–1067) writes state/signature fields and does not call picking actions. A delivered order has picking_status done; after cancellation and reset to draft it retains done, although this module's own calculation (:26–27) specifies in_progress for draft/sent. Quotation badges and filters therefore misclassify the reset order. Register a computed field with state/picking dependencies or cover all order transitions consistently.

Evidence: complete module source, all local calls to the calculation, native order transitions and picking state dependencies read. Source-based lifecycle proof; database reset scenario not executed. Cancellation callbacks also occur before the native final order-state write, so they are not substitutes for an order-state dependency.

## Limits

All native view IDs/anchors checked. Native return creation calls picking confirmation/assignment, which are covered by hooks; no missing-return-hook defect asserted. Service-only orders remaining in progress are not reported because documented scope describes picking completion. No database/browser tests executed.
