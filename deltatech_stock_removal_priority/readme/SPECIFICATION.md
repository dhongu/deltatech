# Technical Specification — deltatech_stock_removal_priority

## Models Extended

### `stock.quant` (`models/stock_quant.py`)

#### Field: `removal_priority`
- Type: `Integer`, `store=True`, computed
- Depends: `product_id`, `location_id`

#### Method: `_compute_removal_priority`
- Reads `stock.removal_priority.default` from `ir.config_parameter` (default: `999`); converts with `int()`, fallback to `999` on `ValueError`/`TypeError`.
- Filters quants to `usage == "internal"`; non-internal quants receive `default_priority`.
- Executes a **single SQL query** to fetch all relevant `stock.putaway.rule` records for the entire batch:
  - Domain: `location_out_id in location_ids AND (product_id in product_ids OR category_id in categ_ids)`
  - Order: `sequence asc`
- Indexes results in two dicts: `(loc_id, product_id) -> sequence` and `(loc_id, categ_id) -> sequence`.
- Assigns priority per quant: product match → category match → default.

#### Method: `_get_removal_strategy_order`
- Returns `"removal_priority, location_id, id"` when `removal_strategy == "priority"`.

#### Method: `_get_gather_domain`
- Extends base domain with `("location_id", "not in", exclude_location_ids)` when `exclude_location_ids` is present in context.

---

### `stock.putaway.rule` (`models/stock_putaway_rule.py`)

#### Purpose
Automatic cache invalidation: recomputes `removal_priority` on affected quants whenever putaway rules change.

#### Method: `_invalidate_removal_priority`
- Searches `stock.quant` by `location_id in location_out_id.ids` and calls `_compute_removal_priority()`.

#### Method: `create` (`@api.model_create_multi`)
- Calls `super().create()`, then `_invalidate_removal_priority()` on new rules.

#### Method: `write`
- Captures `old_loc_ids` before write if any of `sequence`, `product_id`, `category_id`, `location_out_id` are in `vals`.
- After `super().write()`, recomputes quants for union of old and new `location_out_id` values.

#### Method: `unlink`
- Captures `loc_ids` before deletion, calls `_compute_removal_priority()` on affected quants after `super().unlink()`.

---

## Data

### `data/stock_data.xml`
- Defines a `product.removal` record with `method = "priority"` for the removal strategy.

---

## System Parameters

| Key | Default | Description |
|-----|---------|-------------|
| `stock.removal_priority.default` | `999` | Default removal priority for quants without a matching putaway rule |

---

## Context Keys

| Key | Type | Description |
|-----|------|-------------|
| `exclude_location_ids` | `list[int]` | Location IDs excluded from stock gathering in `_get_gather_domain` |

---

## Integration with `deltatech_putaway_strategy`

- `deltatech_putaway_strategy` directs products to sub-locations at receipt via putaway rules (`location_out_id`).
- This module reads the `sequence` of those same rules to assign `removal_priority` to quants stored in `location_out_id`.
- The `exclude_location_ids` context key is consumed by `_get_gather_domain` and produced by `deltatech_putaway_strategy`'s `_action_assign` when `avoid_root_location_on_reservation` is set.
