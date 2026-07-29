## 19.0.1.0.0 (2026-07-29)

- Port of the module from 18.0. The `from_replenishment` flag on `purchase.order` and the
  `stock.rule._make_po_get_domain` override keep replenishment purchase orders separate from the
  ones a buyer creates manually.
- On 19.0 the core grouping of replenishment needs is driven by `res.partner.group_rfq`. With
  `group_rfq = Always` a procurement would otherwise be merged into any draft purchase order of
  the vendor, including manual ones — this module prevents that.
- Added tests covering the flag on generated orders, the merge between successive replenishments
  and the isolation from manual draft orders.
