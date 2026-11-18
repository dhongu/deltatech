## 20.0.0.0.5 (2026-11-18)

- The **Pricelist Lines** button opens the standard pricelist rule search view, extended by this
  module, even when another module adds its own search view (`search_view_id` passed as `[id]`)
  (dhongu/deltatech#3960).
- The screen title is translatable (**Pricelist Rules**, RO *Reguli listă de prețuri*). The **Price**
  column shows the rule, as in the pricelist form (fixed price, discount or surcharge), instead of
  0.00 for *Discount* / *Surcharge* rules; **Fixed Price** and **Price Type** are optional columns.
  The access rights have readable names, also renamed on existing databases (migration)
  (dhongu/deltatech#3953).

## 20.0.0.0.4 (2026-11-04)

- Migration to Odoo 20.0: access rights in `security/ir.access.csv`; the *Pricelist Lines* button
  moved into the standard button box of the price list form.

## 19.0.0.0.4 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.0.0.3 (2026-09-29)

- Own module icon, instead of the generic gears it had.
