Explains, in a read-only dialog, how a reordering rule (`stock.warehouse.orderpoint`)
reached its **forecast** and **to-order** quantity, and flags where it may under- or
over-order because of visibility and horizon limits.

Open it from the **Replenishment** report (Action ▸ *Why this replenishment?*) or from
the **Reordering Rules** form header.

It reconstructs Odoo 18's own computation with live numbers:

- the **decision gate** — forecast at the lead-time date vs Min — that decides *whether* it orders;
- the **order-quantity** math over the visibility window (`max(Min, Max) − forecast`, rounded up
  to the quantity multiple) that decides *how much*;
- the lead-time breakdown (per-rule delays + global Time Horizon) that fixes the lead-time date,
  plus the per-rule **Visibility Days** that extend how far ahead demand is counted.

A visual summary sits at the top of the dialog: an SVG **quantity bar** (forecast vs Min / Max,
with the to-order gap) and a **horizon timeline** (today → lead-time date → visibility window).

It also surfaces risk findings such as: demand scheduled **beyond the visibility window**
(invisible to the order quantity), **no supply route / rule**, **no vendor found** (silent
injected lead time), an **order skipped by the lead-time gate** (gate at/above Min while the
visibility forecast is below it), rounding inflation, manual overrides and snoozes.