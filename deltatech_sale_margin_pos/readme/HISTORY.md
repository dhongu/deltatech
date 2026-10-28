# Changelog

## 19.0.1.0.1 (2026-10-28)

- The POS rows give the *Track Inventory* column of the product, used by the *Storable Products*
  filter of the report (on by default since `deltatech_sale_margin` 19.0.1.3.4); without it the
  POS sales of storable products were hidden by that filter.
- Consultant sheet: the *Storable Products* filter is removed in the steps that show the demo,
  whose products are not storable.

## 19.0.1.0.0 (2026-10-22)

- Point of Sale orders without an invoice in the sale margin report, with the cost computed
  at the closing of the session and, with the commissions, the rates of the point of sale journal.
- Module icon (`icon.svg` + `icon.png`).

- The commission rates of the POS orders are taken from the invoice journal of the point of sale:
  the rates accept only sales journals, and the journal of the POS orders is a miscellaneous one.
- Consultant sheet, usage guide and screenshots.
