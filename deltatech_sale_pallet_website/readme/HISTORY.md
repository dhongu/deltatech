## 19.0.1.0.4 (2026-11-03)

- Description and banner rewritten from the code: the shop follows the
  *Pallet Product* and *Pallet Qty Min* fields of the product, not the
  *Pallet* flag of the product category; removed the checkout rules that the
  module does not have; documented how the cart counts full pallets.

## 19.0.1.0.3 (2026-10-22)

- Listed on Odoo Apps as *Pallet Sales on Website* (was *Sale Pallet Website*). The technical name `deltatech_sale_pallet_website` does not change.

## 19.0.1.0.2 (2026-10-16)

- The pallet lines of the shop cart are now updated before the delivery price and the cart quantity are recalculated, so both include them.
- Removing the last product that needs a pallet from the cart also removes its pallet line.
- Pallet lines added to the cart are marked as generated pallet lines (`is_pallet_line`), like the ones on the sales order.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
