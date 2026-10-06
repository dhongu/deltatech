# Confirmed bugs — 2026-10-03

## LOT-001 — P2: stored lot location is not refreshed when quant quantities change

`models/stock_production_lot.py:13–20` replaces native location_id compute with `_compute_location`, declaring only `quant_ids`. Native `_compute_single_location` depends on both `quant_ids` and `quant_ids.quantity` (`stock_lot.py:167–171`). Updating quantities on already-existing quants does not change relation membership, so the stored location can remain stale when the positive-stock location changes. Include quant quantity/location dependencies needed by the calculation.

Evidence: exact replacement field/method and native decorators inspected; dependency list asserted in `audit_coverage/reproductions/lot_location_contracts.py`. ORM invalidation across existing-quants transfers unexecuted.

## LOT-002 — P2: multiple quants in a single location clear the lot location

`models/stock_production_lot.py:16–18` uses the number of positive quants rather than distinct locations. The same lot/location can have multiple quants distinguished by package or owner, so this clears location_id although all stock is in one location. Native implementation counts `quants.location_id`, preserving this case. Count distinct locations instead.

Evidence: original compute executed on two positive quants sharing location11 returns False. Isolated fixture passed, no database package/owner scenario executed. This is a regression against the native lot location calculation, not merely a custom display preference.

## Limits

Full eligible source read; native lot inverse, move-line view/context and picking lot generation traced. Inherited location inverse remains present; relocation and search/group behavior with a falsely empty/stale location require database validation. Onchange-returned lot domain and dead default-lot-name helper were inspected but not reported separately without a verified client/default invocation scenario. No Odoo/browser tests executed.
