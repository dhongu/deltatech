Open the explanation dialog from either:

- the **Replenishment** report, using Action ▸ *Why this replenishment?* on a reordering rule line, or
- the **Reordering Rules** form, from a button in the form header.

The read-only dialog reconstructs Odoo's own computation with live numbers:

- the **decision gate** — forecast at the lead-time date vs Min — that decides *whether* it orders;
- the **order-quantity** math over the visibility window (`max(Min, Max) − forecast`, rounded up to the quantity multiple) that decides *how much*;
- the lead-time breakdown (per-rule delays + global Time Horizon) that fixes the lead-time date, plus the per-rule **Visibility Days** that extend how far ahead demand is counted.

A visual summary at the top shows an SVG **quantity bar** (forecast vs Min/Max, with the to-order gap) and a **horizon timeline** (today, lead-time date, visibility window).

It also flags risk findings: demand scheduled beyond the visibility window (invisible to the order quantity), no supply route/rule, no vendor found (silent injected lead time), an order skipped by the lead-time gate, rounding inflation, manual overrides and snoozes.
