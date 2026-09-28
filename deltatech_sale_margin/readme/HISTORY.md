# Changelog

## 19.0.1.2.0 (2026-08-20)

- **New: the reaction to a below-cost sale is configurable per company** —
  `res.company.sale_margin_check_mode`, in Settings > Sales > Pricing:

  - `block` (default, unchanged behaviour): the price cannot be saved and the
    order cannot be confirmed, unless the user belongs to the bypass groups;
  - `warn`: nothing is ever blocked. The line is flagged, the order shows a
    banner saying it can still be confirmed, and confirming it leaves a single
    note in the chatter;
  - `off`: no flag, no banner, no block.

  `warn` exists for businesses where selling below cost is a routine part of the
  trade — perishable goods, stock clearance, commercial gestures. Blocking there
  stops the daily work, while the actual need is to make it visible and let the
  seller decide. Existing databases keep the historical behaviour: the default is
  `block` and no migration changes it.

- **New: `sale.order.line.margin_below_limit`** — the line is flagged (orange row
  in the order lines) as soon as the seller leaves the price field, which is where
  the decision is made. The flag is readable by anyone: it says THAT the margin is
  under the limit, not what the cost is, so it does not leak the cost to sellers
  who are not allowed to see it. The figure stays on the native, group-restricted
  `margin_percent`.

- **New: unit guard on the comparison.** `purchase_price` is brought into the line
  unit by `sale_margin` / `sale_stock_margin` through
  `product_id.uom_id._compute_price(...)`. Odoo 19 removed the unit category, so
  that multiplies by the absolute factors without checking the family — the root
  of the kilogram hierarchy is the gram, so a cost of 3.00 per Unit becomes
  3000.00 per kg (measured, not assumed). A product whose `uom_id` is wrong would
  therefore report EVERY line as below cost and the warning would be dismissed as
  noise from day one. The comparison now stays silent when the line unit and the
  product's base unit belong to different families. New helper
  `uom.uom._dt_root_uom()`.

- **New: the margin settings are reachable from the interface.**
  `sale.margin_limit` and `sale.margin_limit_check_validate` existed but were only
  reachable through System Parameters, so in practice nobody configured them. They
  are now exposed in Settings > Sales, next to the reaction mode. `sale.margin_limit`
  doubles as the warning threshold: 0 reports only negative margins, a negative
  value tolerates a loss of up to that percentage, a positive value also reports
  thin but positive margins.

- The onchange modal ("Do not sell below the purchase price") now only appears in
  `block` mode. Where selling below cost is routine, a modal on every line ends up
  being dismissed reflexively without being read; the flagged row carries the same
  signal without interrupting.

- In `warn` mode `check_sale_price` stays silent on purpose. It runs on every
  `write` of a line, so the native `message_post` branch produced one chatter entry
  per keystroke on the price. The decision is now logged exactly once, on
  confirmation.

- `sale_stock_margin` is now a declared dependency. It was already pulled in by
  `auto_install`, but the cost used by the check comes from it (the real valuation
  of the delivery), so the behaviour should not depend on install order.

- **19 tests.** They run as an operator who is OUTSIDE the bypass groups, with a
  dedicated test asserting that: running them as root or admin proves nothing,
  since both belong to `group_sale_below_purchase_price` and the native check would
  not have blocked them either. Each mechanism was validated by sabotage — forcing
  the mode back to `block` breaks 4 tests, removing the chatter note or the banner
  wording breaks 2 more, disabling the unit guard breaks 1.

- Two pre-existing behaviours are now pinned down by tests, because they are easy
  to misread: in `block` mode the block fires from `sale.order.line.write`, so an
  order created through the API with inline lines and confirmed without touching a
  line is NOT blocked; blocking on confirmation requires
  `sale.margin_limit_check_validate`.
