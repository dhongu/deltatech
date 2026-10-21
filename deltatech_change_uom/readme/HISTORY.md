## 19.0.1.0.0 (2026-10-21)

- Migration to 19.0: the purchase unit of measure (`uom_po_id`) no longer exists
  on the product, so the wizard changes only the product unit and also updates
  the vendor pricelist lines (`product.supplierinfo`) that used the old unit;
  `product_uom_id` on sale and purchase order lines, `SQL()` builder for the
  updates, cache invalidated after them; the *Allow to change unit of measure*
  group no longer sets `category_id`.
