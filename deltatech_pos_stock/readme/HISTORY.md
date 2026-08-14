## 19.0.1.0.0 (2026-08-14)

- Migrated to Odoo 19.0.
- Stock loading moved from `product.product` to `product.template`: in 19.0 the POS product card
  receives a template, so `qty_available` has to be loaded on the template.
- Adapted to the 19.0 loading API: `_load_pos_data_fields()` now receives the `pos.config` recordset
  and the removed `_load_pos_data()` hook was replaced by `_load_pos_data_read()`.
- POS JS patch adapted to the 19.0 asset paths (`app/components/product_card`, `app/hooks/pos_hook`)
  and the removed `getProductPriceFormatted()` helper was replaced by `getTaxDetails()` + `formatCurrency()`,
  honouring the `iface_tax_included` setting.
- Card template anchored on `div.product-content`; the `div.product-information-tag` element it used
  to extend no longer exists in 19.0.
