# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## INVENTORY-001 — P1: Inventory is finalized before the conflict wizard resolves stock changes

- **Status:** Fixed in 19.0.2.10.2. `action_apply_inventory()` now returns the `stock.inventory.conflict` action untouched when the core asks for conflict resolution: the inventory stays *In progress*, lines are not marked OK, and the quant keeps its inventory/line links, note and last inventory date. When the wizard is resolved (keep counted quantity or keep difference), the same document is finalized and the inventory move carries the note. Covered by `tests/test_inventory_conflict.py` (cancelled wizard, both resolutions, adjustment without conflict). Priority P1 confirmed.
- **Location:** models/stock_quant.py, action_apply_inventory(), lines 65–100; Odoo stock/models/stock_quant.py, action_apply_inventory().
- **Trigger:** Count a quant, allow an intervening stock movement so is_outdated becomes true, then apply the count.
- **Actual behavior:** The superclass returns the stock.inventory.conflict wizard before applying stock moves. The override still marks lines is_ok, sets the inventory state to done, updates last_inventory_date, and clears inventory links and inventory_note. Closing or cancelling the wizard leaves a completed inventory document without its stock adjustment.
- **Evidence:** Executed the actual override against a superclass returning the standard conflict action. Stock quantity stayed 10, while inventory state became done, the line became is_ok, and inventory links and note were cleared. Verified that the local core implementation returns the wizard before calling _apply_inventory().
- **Impact:** Inventory documents falsely certify unapplied counts; resolving the wizard later can create a separate inventory document because the original links were removed.
- **Suggested fix:** Defer all completion and cleanup until stock application actually succeeds; propagate wizard actions without marking the inventory done, and preserve document links through conflict resolution.
- **Validation needed:** An outdated quant followed by cancelling the wizard, accepting the count, keeping updated stock, and a normal adjustment without conflicts; verify document, move, and note linkage.

## Review limitations

Findings were based on local source inspection and isolated reproductions. INVENTORY-001 was then reproduced and fixed with database-backed tests (2026-10-01).

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **INVENTORY-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.

## INVENTORY-002 — P2: Return quantities use the product default unit rounding

- **Status:** Open; source verified 2026-10-02.
- **Location:** wizard/stock_picking_return.py, `_prepare_stock_return_picking_line_vals_from_move()`.
- **Trigger:** Open a return for a move whose unit differs from the product default unit and has a finer rounding precision.
- **Actual behavior:** `stock_move.quantity` remains in the move unit, but `float_round()` uses `stock_move.product_id.uom_id.rounding`. The core return line uses `move_id.product_uom`; the core return-all action rounds with `stock_move.product_uom.round()`.
- **Evidence:** Executed the actual extracted override with quantity 0.4, move-unit rounding 0.1 and product-unit rounding 1: returned quantity is 0 instead of 0.4. No Odoo database test executed.
- **Impact:** Opening the return dialog can erase a valid fractional quantity or round it upward incorrectly. Users must correct the suggested quantity manually.
- **Suggested fix:** Round the quantity with the move unit used by the return line.
- **Validation needed:** Database regression with different product/move units and both fractional and integral quantities.

## INVENTORY-003 — P1: Inventory documents and lines lack company access rules

- **Status:** Open; source verified 2026-10-02.
- **Location:** security/ir.model.access.csv; security/security.xml; models/stock_inventory.py.
- **Trigger:** A stock operator with access to company A searches the module's inventory document or line models through the ORM/RPC.
- **Actual behavior:** These newly declared models grant stock users read/write/create rights, but the module declares no record rules restricting them to allowed companies. Stock managers additionally have unlink rights. The company fields and relational `check_company=True` checks enforce consistency, not read/write authorization on the document.
- **Evidence:** Inspected all security declarations and verified no module XML defines an `ir.rule`; core stock has no rules for these module-owned models. Odoo 19 `ir.rule._compute_domain()` returns the conjunction of available global rules when no model rules exist.
- **Impact:** Inventory quantities, owners and history from other companies are exposed through these models, and existing documents/lines can be edited outside the intended company scope. Deployment-specific rules from additional addons can mitigate this; the module does not provide them.
- **Suggested fix:** Add global allowed-company rules to both inventory models.
- **Validation needed:** Two-company database tests for search, direct read, create and write with only one company enabled. No database tests executed in this pass.

## INVENTORY-004 — P2: Difference searches ignore their requested comparison value

- **Status:** Open; source verified 2026-10-02.
- **Location:** models/stock_inventory.py, `_search_difference_qty()`.
- **Trigger:** Search lines with `difference_qty = 0`, or `difference_qty != 5`, with `default_inventory_id` in the context.
- **Actual behavior:** The equality branch returns every line of the inventory. The inequality branch always selects nonzero differences. Neither branch uses the requested value.
- **Evidence:** A zero-difference equality domain therefore includes a line with difference 3; a `!= 5` domain excludes a line with difference 0 and includes one with difference 5. The nonzero-difference filter in the commented-out search view uses the supported case; it is not loaded.
- **Impact:** Programmatic searches and custom filters can classify inventory discrepancies incorrectly.
- **Suggested fix:** Implement the actual operator/value comparison or explicitly reject unsupported comparisons.
- **Validation needed:** Equality and inequality domains for zero and nonzero values, including positive and negative differences. No database tests executed.

## INVENTORY-005 — P2: Warehouse product creation uses a removed product type

- **Status:** Open; source verified 2026-10-02.
- **Location:** views/product_view.xml, `action_product_template_warehouse`; views/stock_inventory_views.xml, product-field contexts.
- **Trigger:** Create a product from Warehouse Products or from an inventory product selector.
- **Actual behavior:** These contexts pass `default_type: product`. Odoo 19 product.template.type accepts only consu, service and combo. The Warehouse Products form also hides On Hand whenever `type != product`, so this button is hidden for every valid current product type.
- **Evidence:** Compared action/form XML with the local core selection in product/models/product_template.py. No provider or database calls.
- **Impact:** Product creation can fail on the invalid default, and the dedicated warehouse product form offers no On Hand shortcut for valid goods.
- **Suggested fix:** Use the Odoo 19 goods type and storable flag where appropriate, and base stock-button visibility on current stock fields.
- **Validation needed:** Create storable goods through each context and open an existing storable product in Warehouse Products.

## INVENTORY-006 — P2: Manual location visibility setting does not control the fields

- **Status:** Open; source verified 2026-10-02.
- **Location:** models/res_config_settings.py; views/res_config_settings_view.xml; views/product_view.xml.
- **Trigger:** Disable Show manual location fields in Inventory settings.
- **Actual behavior:** The setting changes membership of group_show_manual_location_fields, but no product/inventory field or enclosing container checks this group. Rack/Row/Shelf/Case remain visible whenever their other context conditions are satisfied.
- **Evidence:** Inspected all module Python/XML references to the group: only the group declaration and settings field refer to it. Product form visibility depends on warehouse context and product type instead.
- **Impact:** The advertised setting has no effect on the product forms, including deployments using putaway rules.
- **Suggested fix:** Apply the visibility group to the intended manual-location fields or containers.
- **Validation needed:** Verify visibility with the setting enabled and disabled, including each warehouse context. No browser/database tests executed.
