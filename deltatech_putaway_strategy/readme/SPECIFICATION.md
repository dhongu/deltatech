# Technical Specification — deltatech_putaway_strategy

## Models Extended

### `stock.location` (`models/stock_location.py`)

#### Fields added
| Field | Type | Description |
|-------|------|-------------|
| `max_products_leaf` | `Integer` | Manual capacity limit for leaf locations |
| `max_products` | `Integer`, computed | Capacity: `max_products_leaf` for leaves, sum of children for parents |
| `current_products` | `Float`, computed | On-hand quantity (from `stock.quant`) |
| `planned_products` | `Float`, computed | Incoming quantity from pending move lines |
| `occupancy_ratio` | `Float`, computed | `current_products / max_products`, clamped to [0, 1] |

#### Method: `_compute_warehouse_occupancy`
- Batched `read_group` on `stock.quant` for all leaf locations in the recordset.
- Bottom-up in-memory aggregation for parent locations.
- Reduces SQL calls from O(N) per leaf to O(1) per batch.

#### Method: `_compute_planned_products`
- Batched `read_group` on `stock.move.line` (state not in `cancel`, `done`) filtered by `location_dest_id`.
- Supports `exclude_move_line_id` context key to exclude a specific line from the calculation.
- Non-leaf locations receive `planned_products = 0.0`.

#### Method: `_check_can_be_used`
- Returns `False` if `max_products_leaf` is set and `current_products + planned_products >= max_products_leaf`.
- Otherwise delegates to `super()`.

#### Method: `_get_putaway_strategy`
- Overrides Odoo's putaway to prefer sub-locations where the same product already exists (if `search_sublocation` system parameter is `True`).
- Searches quants in child locations sorted by `removal_priority, location_id, id`.
- Falls back to standard putaway if no suitable sub-location is found.
- `search_sublocation` parameter is read from `ir.config_parameter` and converted with `.strip().lower() in ("true", "1", "yes")` (no `safe_eval`).

---

### `stock.putaway.rule` (`models/stock_putaway_rule.py`)

#### Fields added
| Field | Type | Description |
|-------|------|-------------|
| `product_id` | `Many2one` → `product.product` | Index added for faster rule lookup |
| `sequence` | `Integer` | Index added for faster ordering |

---

### `stock.move` (`models/stock_move_line.py`)

#### Method: `_action_assign`
- Applies automatic move line splitting based on destination location capacity.
- Excludes root location from reservation if `avoid_root_location_on_reservation` is set on the picking type.
- Loop protection: maximum **100 iterations**; raises `UserError` if exceeded.
- Logging at `DEBUG` level only.
- Cleans up zero-quantity lines after splitting.

#### Method: `_action_done`
- After `super()._action_done()`, checks if destination location exceeds `max_products_leaf`.
- Raises `UserError` if over capacity (last-resort safety barrier).

---

### `stock.move.line` (`models/stock_move_line.py`)

#### Method: `_apply_putaway_strategy`
- Skips putaway if `avoid_putaway_rules` context key or picking type flag is set.

#### Method: `_split_by_putaway_capacity`
- For each line, computes available capacity: `max_products_leaf - (current_products + planned_products)`.
- If `qty_available < 0`: sets line quantity to 0, creates a new line for the full quantity at the move's destination.
- If `0 < qty_available < line.quantity`: splits line, creates a new line for the remainder.
- New lines are re-routed via `_apply_putaway_strategy` with `exclude_location` context to avoid re-selecting full locations.
- Returns `(is_split: bool, to_reprocess: stock.move.line recordset)`.

---

### `stock.picking.type` (`models/stock_picking.py`)

#### Fields added
| Field | Type | Description |
|-------|------|-------------|
| `avoid_putaway_rules` | `Boolean` | Disables putaway rule application for this operation type |
| `avoid_root_location_on_reservation` | `Boolean` | Excludes the root source location from stock reservation |

---

## System Parameters

| Key | Default | Description |
|-----|---------|-------------|
| `deltatech_putaway_strategy.search_sublocation` | `False` | Enable sub-location search for existing product stock during putaway |

---

## Context Keys

| Key | Type | Description |
|-----|------|-------------|
| `avoid_putaway_rules` | `bool` | Skips putaway strategy application |
| `exclude_location` | `stock.location` recordset | Locations excluded from putaway destination selection |
| `exclude_location_ids` | `list[int]` | Location IDs excluded from stock reservation (consumed by `deltatech_stock_removal_priority`) |
| `exclude_move_line_id` | `int` | Move line ID excluded from planned quantity calculation |

---

## Integration with `deltatech_stock_removal_priority`

- This module produces `exclude_location_ids` in context (via `_action_assign`) when `avoid_root_location_on_reservation` is active.
- `deltatech_stock_removal_priority` consumes `exclude_location_ids` in `_get_gather_domain`.
- Putaway rule `sequence` values set by this module are read by `deltatech_stock_removal_priority` to compute `removal_priority` on quants.
