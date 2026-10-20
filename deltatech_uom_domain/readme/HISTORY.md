## 20.0.1.2.0 (2026-10-20)

- Default purchase unit on the product (`purchase_uom_id`, Purchase tab), restricted
  to the units of the product unit's reference tree, as `uom_po_id` was before 19.0.
  New vendor pricelist lines take it by default, and a purchase order line takes it
  when the vendor has no valid pricelist line (missing, expired or for another
  vendor); a valid vendor line keeps priority. Both lines still offer every unit of
  the same tree (`uom_id` on both on 20.0). Odoo 19 removed `uom_po_id`: a new vendor
  line came out in the product unit, and without a valid vendor line the order fell
  back to the product unit, so 4.894 m³ of timber were received as 4.894 pieces.

## 20.0.1.1.2 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

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
