# Bug review — deltatech_putaway_strategy

Review date: 2026-10-02. Target version: Odoo 19.

## PUTAWAY-001 — P2: A completely full destination is not split or reassigned

- **Status:** Open.
- **Location:** models/stock_move_line.py, _split_by_putaway_capacity().
- **Trigger:** A move line targets a leaf whose current plus other planned quantity equals its capacity.
- **Actual behavior:** qty_available is zero. The negative-space branch does not run and the split condition requires qty_available to be truthy, so a positive line remains assigned to a completely full destination.
- **Evidence:** Actual AST-extracted method with capacity/current=10 and line quantity=5 returns is_split=False and leaves quantity=5. Mock location only.
- **Impact:** Reservation can retain impossible capacity assignments. Final validation checks move.location_dest_id, so a root move destination can also miss the actual leaf used by its lines.
- **Suggested fix:** Treat zero available capacity like negative capacity and reroute the whole line; validate actual move-line destinations.
- **Validation needed:** Zero/negative space, multiple destination lines under a root and positive remaining capacity; no positive assignment should remain at a full leaf.

## PUTAWAY-002 — P2: Planned occupancy and splitting compare quantities in different units

- **Status:** Open.
- **Location:** models/stock_location.py, _compute_planned_products(); models/stock_move_line.py, _split_by_putaway_capacity().
- **Trigger:** Incoming move lines use a unit other than the product base unit, for example dozen versus pieces.
- **Actual behavior:** Current occupancy sums stock.quant.quantity (product units), planned occupancy sums stock.move.line.quantity (line units), and split sizes compare raw line.quantity with available capacity derived from base-unit quants.
- **Evidence:** Compared complete code with core stock.move.line.quantity_product_uom compute, which explicitly converts product_uom_id to product.uom_id. These custom aggregation/split paths use no conversion. One planned dozen is counted as one instead of twelve pieces. Source evidence; no warehouse database execution.
- **Impact:** Capacity decisions can undercount pending stock or split incorrect physical quantities.
- **Suggested fix:** Define the capacity unit policy, aggregate converted quantities and convert available capacity back into each line unit for splitting.
- **Validation needed:** Unit/Dozen, mixed line units and a product base unit with a non-unit factor; compare physical capacity before/after split.

## PUTAWAY-003 — P2: Avoid-root reservation option relies on an undeclared addon

- **Status:** Open.
- **Location:** __manifest__.py; models/stock_move_line.py, StockMove._action_assign().
- **Trigger:** Install only this addon and declared stock dependency, then enable Avoid Root Location on Reservation.
- **Actual behavior:** The option only supplies exclude_location_ids in context. Local core stock.quant does not consume this key; the sole local consumer is deltatech_stock_removal_priority, which is not a dependency.
- **Evidence:** Read manifest, option help and context hook; searched core stock.quant and inspected removal-priority _get_gather_domain, which adds the exclusion. No reservation executed.
- **Impact:** The enabled option can silently leave root stock eligible for allocation on a supported minimal installation.
- **Suggested fix:** Declare the consuming addon or implement the exclusion within the dependency closure; hide/disable unsupported options explicitly if optional.
- **Validation needed:** Minimal declared-dependency installation and installation with removal-priority, flagged/unflagged operations and root-versus-shelf stock.

## Review limitations

All eligible source was read. Reproductions use actual AST-extracted methods with mock location/validation/logging objects. No Odoo stock mutations, database integration tests or live access probes executed.
