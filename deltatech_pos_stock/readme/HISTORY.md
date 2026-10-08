## 19.0.1.2.0 (2026-10-08)

- New POS setting **Quantity shown**: the badge can display the stock *on hand* (the default,
  unchanged behaviour) or the *available* quantity, which subtracts what is already reserved
  for orders that have not left the warehouse yet. Needed wherever the picking is validated by
  the warehouse rather than at the till — on hand does not move until then, so the cashier
  would otherwise be looking at stock that is already sold.
- `free_qty` is now computed on `product.template` by summing its variants. Core aggregates
  `qty_available` and the forecast onto the template but stops short of the free quantity, and
  the POS card is handed a template.
- `stock.quant` also notifies open sessions when `reserved_quantity` changes, so the available
  badge keeps up. Restricted to the registers actually showing the available quantity:
  reservations move with every sale, and registers left on "on hand" must not be woken up.
- Products with nothing left to sell show the quantity in red, and adding one raises a warning
  in the register. The sale still goes through — a hard block would stop the cashier whenever
  the figure in Odoo is behind.

## 19.0.1.1.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.1.0 (2026-08-19)

- Fixed stale stock badge: `qty_available` is a non-stored computed field, so a sale (which
  writes on `stock.quant`, not on `product.template`) never bumps the template's `write_date`.
  The POS incremental sync filters on `write_date`, so it never re-sent the recalculated
  quantity to sessions already open — the badge could stay frozen at a days-old value.
- `stock.quant` now pushes a live `STOCK_SYNCHRONISATION` bus notification (reusing the same
  `pos.bus.mixin` channel core uses for `notify_synchronisation`) whenever a product's on-hand
  quantity changes, to every open POS session with `display_stock` enabled. The frontend
  subscribes to it and merges the fresh `product.template` data straight into the in-memory
  model, independent of the `write_date`-based sync.

## 19.0.1.0.0 (2026-08-14)

- Migrated to Odoo 19.0.
- Stock loading moved from `product.product` to `product.template`: in 19.0 the POS product card
  receives a template, so `qty_available` has to be loaded on the template.
- Adapted to the 19.0 loading API: `_load_pos_data_fields()` now receives the `pos.config` recordset
  and the removed `_load_pos_data()` hook was replaced by `_load_pos_data_read()`.
- POS JS patch adapted to the 19.0 asset paths (`app/components/product_card`, `app/hooks/pos_hook`)
  and the removed `getProductPriceFormatted()` helper was replaced by `getTaxDetails()` + `formatCurrency()`,
  honouring the `iface_tax_included` setting.
- Card template anchored on `div.product-content`; the `div.product-information-tag` element it used
  to extend no longer exists in 19.0.
- Added a POS frontend test asserting that the badge renders both the price and the on-hand quantity.
