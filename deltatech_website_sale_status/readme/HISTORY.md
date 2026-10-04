## 19.0.2.0.11 (2026-10-04)

- Fix: a website quotation sent to the customer never reached the `placed`
  stage — the `else` of the next if/elif/else reset it to `in_process`.
- Fix: the stage set from the carrier status of the transfer (`write()` on
  `stock.picking`) was overwritten at once by the recompute, since
  `delivery_state` is a dependency of the stage. For storable products the
  order never reached `pre_advice`/`in_delivery` and became `delivered` at the
  validation of the transfer, while the parcel was still with the carrier —
  in the portal too. The `write()` override is gone; `_compute_stage` now
  applies the carrier status over the `to_be_delivery`/`delivered` stock
  stages: `pre_advice` when an AWB was generated, `in_delivery` while the
  parcel is with the carrier (`in_transit`/`in_warehouse`/`in_delivery`),
  `delivered` when the carrier delivered all the transfers. A post-migration
  recomputes the stage of the orders it changes.
- Fix: the portal filters used the stage value `cancel` instead of
  `canceled`: the "Canceled" filter never matched and "Open/Closed Orders"
  did not treat canceled orders as closed. "Canceled" and "Closed Orders" now
  also list the canceled orders, left out of the standard order list.
- The `rfq` and `pre_advice` stages are added to the sales report and get a
  badge in the portal order list.

## 19.0.2.0.10 (2026-10-04)

- Extend unit tests to cover the order stage computation, the stage set from the
  delivery state of the transfer, the stage in the sales report and the portal
  order list (status filters, stage sorting, pager).

## 19.0.2.0.9 (2026-09-29)

- Own module icon, instead of the generic gears it had.

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
