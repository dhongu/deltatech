## 20.0.1.0.3 (2026-11-04)

- Migration to Odoo 20.0: the product currency rule is also applied in SQL
  (`_compute_sql_currency_id`) so search, grouping and ordering use the price list currency; tests
  on the 20.0 pricelist rules (`discount`).
- Dead code removed: `models/pricelist.py` (never imported) and the never-loaded
  `views/pricelist_view.xml` / `views/product_view.xml` (dhongu/deltatech#3959).

## 19.0.1.0.3 (2026-11-03)

- Description rewritten from the code: the price list currency is set per company (default EUR), not per product.
- Documented that on installation all companies get EUR as price list currency.
- Summary and banner corrected; removed the readable discount formula on price rules, which is not active.

## 19.0.1.0.2 (2026-10-22)

- Listed on Odoo Apps as *Pricelist Currency Extension* (was *Price List Currency Extension*). The technical name `deltatech_pricelist` does not change.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
