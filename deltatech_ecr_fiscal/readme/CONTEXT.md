The fields used to be defined twice, identically: on `pos.order` in `deltatech_pos` and on
`account.move` in `deltatech_sale_store`. Any module that only needed to read the receipt number
had to depend on one of them, and so on the whole cash register suite.

The contract now lives in a module that depends only on `account`. The cash register modules
still **write** the fields; any other module can **read** them without pulling in the driver.
`point_of_sale` is not a dependency either: the mixin on `pos.order` is applied by
`deltatech_pos`, so `deltatech_sale_store`, the store alternative without POS, does not need
Point of Sale to reach the fields.

On install, a `pre_init_hook` takes over the `ir_model_data` rows of the two former owners, so
updating them does not drop the columns and the fiscal receipt numbers already recorded.
