## 19.0.1.0.0

- Ported from 18.0. No code changes: the `product.pricelist.item.base`
  selection value and the `standard_price_with_vat` compute fields on
  `product.template`/`product.product` use APIs unchanged in Odoo 19. In use
  in production at Ridacon (helpdesk ticket #9538); the migration script was
  about to uninstall it, which would have silently reset any pricelist rule
  based on "Cost with VAT" to the field's default base.
