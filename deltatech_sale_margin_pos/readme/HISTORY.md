# Changelog

## 19.0.1.1.0 (2026-11-18)

- The credit note issued from a Point of Sale return of a receipt (the sale was not invoiced, so
  the credit note reverses no invoice) takes its cost from the Point of Sale: the cost of the
  returned goods, which is the cost of the original sale. Until now it had a cost of 0 and the
  *Profit analysis* report showed the whole value of the return as a loss. The cost of the lines
  already invoiced is corrected with the *Update Purchase Price* wizard.

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
