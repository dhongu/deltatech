## 20.0.1.0.0 (2026-11-09)

- Migration to Odoo 20.0: the price types follow the 20.0 pricelist rules, **Discount** (on the
  sales price or another pricelist), **Surcharge** (on the sales price, the cost or another
  pricelist) and **Fixed Price**, with rounding, added amount and margins for both percentages;
  access rights in `security/ir.access.csv`; screenshots regenerated on 20.0.

## 19.0.1.0.0 (2026-11-09)

- New module: add pricelist rules for many products, variants or categories at once, and
  apply the same price computation, minimum quantity or validity period to many rules.
- A rule based on its own pricelist is refused for every price type (also Discount on a
  pricelist), in both wizards; existing rules are found with one search for all the products.
