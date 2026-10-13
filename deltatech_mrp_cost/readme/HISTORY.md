## 19.0.2.0.8 (2026-10-08)

- Fixed MRPCOST-001: printing the production order of a done manufacturing
  order failed, because the *Finished Products* table and the component
  amounts still read the stock valuation layers removed in Odoo 19. Both now
  use the stock move value.

## 19.0.2.0.7 (2026-09-29)

- Own module icon, instead of the generic gears it had.
