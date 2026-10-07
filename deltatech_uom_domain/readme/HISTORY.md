## 19.0.1.1.0 (2026-10-07)

- Vendor pricelist lines (`product.supplierinfo`) now restrict the vendor unit
  to the product unit, its packagings and the units of the same reference tree.
  Standard Odoo 19 puts no domain on this field, so a unit of another tree was
  accepted silently: "ml" (millilitre) on a product in metres turned 22.5 m
  into 22,500 ml on the generated RFQ.

## 19.0.1.0.1 (2026-09-30)

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.0 (2026-09-29)

- Add: offer every unit sharing the product unit's reference tree on purchase order lines and invoice lines, restoring the pre-19.0 category-based selection that Odoo replaced with the per-product `uom_ids` list.
