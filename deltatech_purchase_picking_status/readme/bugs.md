# Confirmed bugs — 2026-10-03

## PURPICKSTATUS-001 — P2: search domain contradicts displayed cancelled-order status

`models/purchase_order.py:48` restricts the candidate universe to state != cancel for every supported operator. The computation has no such exclusion: a cancelled order with all receipts done/cancel has status done, and a cancelled order without receipts has status in_progress. Searching either displayed value can never return these records; negated searches also omit them. The domain for a computed-field search must represent the field predicate, leaving independent state filters to callers. Remove the unconditional candidate exclusion or align the field semantics explicitly.

Evidence: all source read, positive/negative search branches compared with compute branches. ORM access remains applied by self.search; this is a result-consistency defect, not a permissions bypass. Source reasoning only; database domains not executed.

## PURPICKSTATUS-002 — P2: nonstored calculation lacks cache invalidation dependencies

The computed picking_status field and `_compute_picking_status` declare no dependencies. Once read in an Environment, changing order.state or picking_ids.state does not invalidate its cached value. For example read a service RFQ as in_progress, confirm it in the same Environment, then read picking_status again: the computation's intended done value is not scheduled/refreshed. Add dependencies on state, picking_ids and picking_ids.state.

Evidence: native fields.get_depends (:561–599) collects only declared/decorated dependencies, none exist here; models.modified (:6769–6845) invalidates nonstored fields through dependency triggers. Native purchase picking_ids is stored and depends on order_line.move_ids.picking_id. Source-supported cache defect; a fresh request can mask it and a database transaction reproduction was not executed.

## Limits

Native purchase view IDs/anchors checked. Operator normalization fix handles scalar equality and collection membership; not reported as broken. Search scans all accessible non-cancelled orders in Python; no performance severity asserted without measurements. No database/UI tests executed.
