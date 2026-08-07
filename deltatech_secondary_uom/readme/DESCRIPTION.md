This module adds **product specific conversion factors** between units of
measure, following the SAP material master (MARM) pattern.

In standard Odoo 19 the conversion factor belongs to the unit of measure
itself, so "1 box = 12 units" is global. With this module the factor is
defined **per product**, on the *Alternative Units* tab of the product form:

- `3 m² = 4 Units` — each piece covers 0.75 m²
- `1 kg = 2 Units` — each piece weighs 0.5 kg

The stock is always kept in the product **base unit**. On sale order lines,
purchase order lines and stock moves the user can enter the quantity in an
alternative unit (kg, m², ...) and the line quantity is computed
automatically — and vice versa: changing the line quantity updates the
secondary quantity.

The **price always stays in the base unit**: the secondary quantity is only
an input/information helper, it never affects pricing, invoicing or stock
valuation.

Unlike creating dedicated UoM records per product, this approach keeps the
global UoM table clean and does not affect standard reports, stock valuation
or any code reading `uom.factor` directly in SQL.
