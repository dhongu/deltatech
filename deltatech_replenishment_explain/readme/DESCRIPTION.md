Explains, in a read-only dialog, how a reordering rule (`stock.warehouse.orderpoint`)
reached its **forecast** and **to-order** quantity, and flags where it may under- or
over-order because of visibility and horizon limits.

Open it from the **Replenishment** report (Action ▸ *Why this replenishment?*) or from
the **Reordering Rules** form header.

It reconstructs Odoo's own computation with live numbers:

- the forecast build-up (on hand + scheduled receipts − scheduled demand, up to the lead horizon);
- the order-quantity math (`max(Min, Max) − forecast`, rounded up to the replenishment multiple);
- the lead-time + Replenishment Horizon breakdown that fixes the lead-horizon date;

A visual summary sits at the top of the dialog: an SVG **quantity bar** (forecast vs Min / Max,
with the to-order gap) and a **horizon timeline** (today → lead time → lead-horizon date).

It surfaces risk findings such as: demand scheduled **beyond the horizon** (invisible to the
forecast), **no vendor found** (silent +365 days), a **potential stockout** even when nothing is
ordered (deadline set), rounding inflation, manual overrides and snoozes.
