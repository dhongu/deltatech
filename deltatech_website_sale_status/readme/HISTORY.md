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
