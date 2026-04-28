# Deltatech Putaway Strategy

This module extends Odoo's inventory management with location capacity tracking and smarter putaway decisions. It ensures products are always directed to locations that have available space, and automatically handles overflow by splitting move lines when needed.

Designed to work together with **deltatech_stock_removal_priority**: putaway rules direct products to specific sub-locations at receipt, and that module uses those same rules to determine the removal order at picking time.

## Key Features

- **Location Capacity Management**:
  - Define a maximum number of products for each leaf storage location.
  - Computed capacity is automatically aggregated up the location hierarchy.
  - Track current on-hand quantity and planned incoming quantity per location.
  - Visualize occupancy ratio for each location.

- **Smarter Putaway**:
  - Respects capacity limits when suggesting destination locations.
  - Prefers locations where the same product is already stored (configurable).
  - Automatically splits move lines when a destination location reaches its maximum capacity.
  - Protected against infinite loops during split operations.

- **Operation Type Controls**:
  - Per operation type: optionally disable putaway rules.
  - Per operation type: optionally exclude the root source location from stock reservation.

## Usage

1. Set **Max products (leaf)** on leaf locations that should have a maximum capacity.
2. Use standard operations (receipts, internal transfers). The putaway helper will:
   - reject over-capacity destinations,
   - split move lines automatically when needed,
   - and try to choose a location with existing stock first when appropriate.
3. The computed capacity fields can be displayed in location views or used by other modules (e.g., visual warehouse map).

## Configuration

- To enable sub-location search (prefer locations with existing stock), go to **Settings > Technical > System Parameters** and set ``deltatech_putaway_strategy.search_sublocation`` to ``True``.
- To disable putaway rules for a specific operation type, open **Inventory > Configuration > Operations Types** and enable **Avoid Putaway Rules**.
- To exclude the root source location from reservation, enable **Avoid Root Location on Reservation** on the operation type.

## Compatibility

- Odoo 18.0.
- Compatible with Odoo's standard storage category rules (max weight, product/pack capacities, allow new product rules, etc.).
- Designed to work alongside modules that display warehouse maps or dashboards (e.g., `deltatech_warehouse_map`).
