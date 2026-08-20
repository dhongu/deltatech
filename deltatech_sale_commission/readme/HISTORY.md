# Changelog

## 19.0.1.5.0 (2026-08-20)

- `account.move.line._check_sale_price` now honours the company policy
  `res.company.sale_margin_check_mode` from `deltatech_sale_margin`. It used to
  raise unconditionally, which meant a company allowed to sell below cost would
  pass the sale order and then hit the wall at invoicing — once the goods were
  already delivered. The constraint still blocks in `block` mode, which stays the
  default.
