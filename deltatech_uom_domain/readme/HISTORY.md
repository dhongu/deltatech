## 19.0.1.2.0 (2026-10-20)

- Default purchase unit on the product (`purchase_uom_id`, Purchase tab), restricted
  to the units of the product unit's reference tree. When it is set, it is the only
  unit offered on vendor pricelist lines and purchase order lines, and both take it
  by default. Odoo 19 removed `uom_po_id`: a new vendor line came out in the product
  unit, and without a valid vendor line the order fell back to the product unit, so
  4.894 m³ of timber were received as 4.894 pieces.

## 19.0.1.1.2 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 19.0.1.1.1 (2026-10-09)

- Apps Store banner (banner.json).

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
