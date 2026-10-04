# Changelog

## 20.0.1.5.5 (2026-10-04)

- COMMISSION-003 (security): the commission rates (`commission.users`) had no company rule, so a Commission Manager allowed only in company A could read, change, delete or create the rates of company B (salesperson, manager and director rates). A multi-company restriction now limits the rates to the allowed companies, and moving a rate to another company requires access to that company.
- Port of 19.0.1.6.2 (dhongu/deltatech#3116). In 20 the company rule is a global row (no group, `crud`) of `security/ir.access.csv` instead of an `ir.rule` in the `noupdate` `security/security.xml`, so it is also updated on module upgrade.

## 20.0.1.5.4 (2026-10-01)

- [FIX] in "block" mode, the invoice of a confirmed sale order is no longer refused with "You can not sell below the purchase price." when the line is invoiced at the price of its order line: that price was already judged on the order, possibly by a seller allowed to sell below cost. A price changed on the invoice, and invoice lines without an order, are still checked.

## 20.0.1.5.3 (2026-10-01)

- Margin report: the quantity of an invoice line in another unit than the product
  unit is converted with the right ratio. Two dozen of a product sold by the unit
  now show as 24 units (they showed as 1/6). Refunds keep their sign.

## 19.0.1.5.2 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.

## 19.0.1.5.0 (2026-08-20)

- `account.move.line._check_sale_price` now honours the company policy
  `res.company.sale_margin_check_mode` from `deltatech_sale_margin`. It used to
  raise unconditionally, which meant a company allowed to sell below cost would
  pass the sale order and then hit the wall at invoicing — once the goods were
  already delivered. The constraint still blocks in `block` mode, which stays the
  default.
