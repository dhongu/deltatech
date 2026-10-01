# Changelog

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
