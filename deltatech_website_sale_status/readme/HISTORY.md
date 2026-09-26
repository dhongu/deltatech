## 18.0.2.0.4 (2026-09-26)

- Fix: the order stage failed to compute (`AttributeError: purchase_order_count`)
  on databases without `sale_purchase`, which is not a dependency of this
  module. The branch that marks a web order as `rfq` when its purchase RFQ was
  sent now runs only when `sale_purchase` is installed. No new dependency: it
  would install Purchase on every web shop at the next update. Found by the
  sharded CI, where the website addons are installed without `sale_purchase`.
