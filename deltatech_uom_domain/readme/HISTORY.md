## 20.0.1.1.1 (2026-10-09)

- Apps Store banner (banner.json).

## 20.0.1.1.0 (2026-10-07)

- Vendor pricelist lines (`product.supplierinfo`) now restrict the vendor unit
  to the units available on the product (`_get_available_uoms()`, with the
  per-variant `extra_uom_ids` on 20.0) and the units of the same reference
  tree. Standard Odoo puts no domain on this field, so a unit of another tree
  was accepted silently: "ml" (millilitre) on a product in metres turned 22.5 m
  into 22,500 ml on the generated RFQ.

## 20.0.1.0.1 (2026-10-02)

- Migration to Odoo 20.0: no code change needed; the extension still runs after
  the standard computation, so the 20.0 additions (`extra_uom_ids` per variant,
  the multi-UoM feature check) are kept. Test for the vendor unit being preserved.

## 19.0.1.0.1 (2026-09-30)

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.0 (2026-09-29)

- Add: offer every unit sharing the product unit's reference tree on purchase order lines and invoice lines, restoring the pre-19.0 category-based selection that Odoo replaced with the per-product `uom_ids` list.
