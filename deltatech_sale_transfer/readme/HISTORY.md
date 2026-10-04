## 20.0.1.0.2 (2026-10-04)

- Fixed: the transfer request created on sale confirmation mixed the sale line unit with the
  product unit. For 1 Dozen ordered with 6 Units in the sale warehouse it computed 1 - 6, found no
  shortage and created no transfer; in other cases it could request more than the source warehouse
  had. Shortage and source availability are now computed in the product unit and the transfer move
  is created in the product unit (before: in the sale line unit). Repeated lines of the same
  product no longer count the same destination/source stock twice (SALETRANSFER-001). Transfer
  quantities change whenever the sale unit differs from the product unit or a product is repeated.
  Port of 19.0.1.0.2 (dhongu/deltatech#3118); on 20.0 the move unit is `stock.move.uom_id`
  (19.0: `product_uom`).

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
