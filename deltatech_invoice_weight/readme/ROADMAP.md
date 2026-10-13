## Retire `l10n_ro_net_weight`

Goal: stop defining and reading `product.template.l10n_ro_net_weight`; follow the Odoo model instead
(`product.weight` = weight of the product, i.e. net; gross = net + packaging).

1. Delete `models/product_template.py` and its import from `models/__init__.py`.
2. Compute the document weights from `product.weight`, converting the line quantity with
   `product_uom_id._compute_quantity(qty, product.uom_id)` (sale: `product_qty`, purchase: `product_uom_qty`).
3. Turn `weight`, `weight_net` on `account.move` into stored computed fields with `@api.depends`
   (lines, quantity, product, UoM); gross = net + packaging taken from `stock_move_ids` / package
   `shipping_weight`, falling back to net when there is no transfer. Decide whether `weight_package`
   stays (derived) or is removed.
4. Same for `sale.order` / `purchase.order` (net only, or gross = net).
5. Fix the report label ("New weight" -> "Net weight") and show the weight UoM.
6. Tests: UoM conversion, line change recalculation, packaging, credit note, variants, report,
   installation without `l10n_ro_stock`.
7. Data: values already stored in `product_template.l10n_ro_net_weight` stay in the database (nothing
   reads them any more); check customers where it differs from `weight` before releasing.
8. Port to 20.0 afterwards.

Customers depending on this module: `terrabit_agroamat`, `terrabit_datus`.
