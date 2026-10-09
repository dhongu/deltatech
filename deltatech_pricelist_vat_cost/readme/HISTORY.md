## 19.0.1.0.4 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.0.3

- In multi-company, cost with VAT uses only the purchase taxes of the current
  company. A shared product carrying the default purchase tax of several
  companies had all of them applied at once (cost 100 with a 21% and an 11%
  tax was reported as 132 instead of 121), and so did the pricelists based
  on it (VATCOST-002). The value is also recomputed per company instead of
  reusing the one computed for another company in the same transaction.

## 19.0.1.0.2

- Cost with VAT now depends on the purchase taxes only: a product with
  purchase taxes but no sales taxes was reported at cost without VAT, and so
  were the pricelist rules based on "Cost with VAT" (VATCOST-001). The value
  is also recomputed when the purchase taxes, their amount or type, or the
  currency change.

## 19.0.1.0.1

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.0

- Ported from 18.0. No code changes: the `product.pricelist.item.base`
  selection value and the `standard_price_with_vat` compute fields on
  `product.template`/`product.product` use APIs unchanged in Odoo 19. In use
  in production at Ridacon (helpdesk ticket #9538); the migration script was
  about to uninstall it, which would have silently reset any pricelist rule
  based on "Cost with VAT" to the field's default base.
