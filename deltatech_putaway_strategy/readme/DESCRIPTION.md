# Deltatech Putaway Strategy

This module extends Odoo Inventory locations with simple capacity tracking and enhances the putaway decision logic.

## Key features
- Adds capacity fields on `stock.location`:
  - `Max products (leaf)`: manual capacity for leaf locations.
  - `Max products`: computed capacity for any location (sum of children for non‑leaf locations).
  - `Current quantity`: computed on‑hand quantity per location.
  - `Planned quantity`: computed incoming quantity per location based on pending moves.
  - `Occupancy`: computed ratio `current/max` (clamped to [0, 1]).
- Optimized computation for large hierarchies:
  - Single batched `read_group` on `stock.quant` for all leaf locations in the batch.
  - Batched `read_group` on `stock.move.line` for planned quantities.
  - Bottom‑up in‑memory aggregation for parent locations.
- Smarter putaway:
  - Respects capacity on leaf locations when suggesting destinations.
  - Automatically splits move lines if a destination location reaches its maximum capacity.
  - Prefers empty child locations when possible (if search sublocation is enabled).
  - Optimized rule lookup with database indexes on `product_id` and `sequence` for `stock.putaway.rule`.
  - Keeps full compatibility with Odoo’s storage category rules (max weight, product/pack capacities, allow new product rules, etc.).

## Usage
1. Set `Max products (leaf)` on leaf locations that should have a maximum capacity.
2. Use standard operations (receipts, internal transfers). The putaway helper will:
   - reject over‑capacity destinations,
   - and try to choose an empty child location first when appropriate.
3. The computed fields can be shown in location tree or used by other modules (e.g., visual warehouse map).

## Performance notes
- The occupancy compute reduces SQL calls from O(N) per leaf to O(1) per batch using a single `read_group`, mirroring the efficient pattern from Odoo’s `_compute_weight`.

## Compatibility
- Designed to work alongside modules that display warehouse maps or dashboards. The module `deltatech_warehouse_map` can depend on this one to display the capacity and occupancy KPIs.

## Tests
- Includes TransactionCase tests that validate:
  - capacity enforcement via `_check_can_be_used`,
  - putaway preference for empty child locations via `_get_putaway_strategy`,
  - automatic splitting of move lines when capacity is reached,
  - planned quantity calculations.

## Screenshots
The app store gallery uses the images from `static/description/`.
