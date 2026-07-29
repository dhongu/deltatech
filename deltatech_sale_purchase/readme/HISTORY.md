## 19.0.1.0.0 (2026-07-29)

- Port of the module from 18.0. Cancelling a sale order still removes the purchase lines it
  generated, as long as their purchase order is still a draft.
- `sale.order._action_cancel` now works on the whole recordset of generated purchase lines instead
  of assuming a single one, so an order whose moves feed several purchase lines no longer raises a
  singleton error.
- Dropped the `stock.rule._make_po_get_domain` override that neutralized the procurement group:
  `group_propagation_option` no longer exists on 19.0, where the grouping of replenishment needs is
  driven by `res.partner.group_rfq` instead. Set that field to `Always` to collect the needs of
  several sale orders into a single draft purchase order.
- Dropped the `_log_decrease_ordered_quantity` override as well. On 19.0 core propagates a decrease
  of the ordered quantity to the draft purchase line by itself and logs no exception activity, so
  the override had no effect left. A test guards that core behaviour, so the override can be
  restored if it ever changes.
- Replaced the tests: the previous ones asserted nothing and exercised the removed override.
