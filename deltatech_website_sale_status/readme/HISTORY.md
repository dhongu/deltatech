## 19.0.2.0.8 (2026-09-26)

- Fix: the order stage failed to compute (`AttributeError: purchase_order_count`)
  on databases without `sale_purchase`, which is not a dependency of this
  module. The branch that marks a web order as `rfq` when its purchase RFQ was
  sent now runs only when `sale_purchase` is installed. No new dependency: it
  would install Purchase on every web shop at the next update. Found by the
  sharded CI, where the website addons are installed without `sale_purchase`.

## 19.0.2.0.7 (2026-09-24)

- Fix: the 18.0→19.0 migration (#2227) dropped `models/stock_picking.py` in
  full — the `write()` override that set `sale_order.stage` from the
  picking's `delivery_state` (`pre_advice`/`in_transit`/`in_warehouse`→
  `in_delivery`, `delivered`→`delivered`). The `rfq` and `pre_advice` values
  of the `stage` selection, the `_compute_stage` branch that set `rfq` when
  a linked purchase RFQ was sent, and the `_action_confirm` override that
  forced a `stage` recompute on order confirmation went with it — same
  migration commit that also dropped the portal filters (restored earlier,
  see 19.0.2.0.5's predecessor). None of this was ever documented as an
  intentional removal. Restored all of it verbatim from 18.0.

## 19.0.2.0.6 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.

## 19.0.2.0.5 (2026-07-23)

- Fix: the "Phone" search field added to the sale order search view
  (`view_sales_order_filter`) still referenced `partner_id.mobile`, a field
  removed from `res.partner` in Odoo 19 (only `phone` remains). Since this
  field is named `partner_id` like the native one, it gets auto-populated by
  the `search_default_partner_id` context — used, among others, by the
  "Sales" button in the bank reconciliation widget — which raised
  `ValueError: Invalid field res.partner.mobile` on every use. The filter now
  only matches on `partner_id.phone`.
