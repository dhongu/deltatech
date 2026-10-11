# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## SIMPLE-001 — P1: Multiple output lines each receive the entire consumed cost

- **Status:** Fixed in 19.0.1.1.3. `_allocate_finit_price()` splits the consumed cost once, by standard value (standard price x quantity in the product unit), or by quantity when no standard price is set; the last line absorbs the rounding; zero-quantity lines get price 0. Used by the form button and the line onchange. Covered by `test_cost_split_over_several_received_products`, `test_cost_split_by_quantity_without_standard_price`, `test_single_received_product_keeps_whole_cost`.
- **Location:** models/mrp_simple.py, compute_finit_price() and MRPSimpleLineIn.compute_finit_price().
- **Trigger:** Produce two or more output lines and recompute their prices, or change an output quantity in the form.
- **Actual behavior:** The full input cost is divided by each output line quantity independently. Therefore each output line has a value equal to the complete input cost; summed output value multiplies cost by the number of output lines.
- **Evidence:** Executed the actual parent recomputation method extracted by AST: consumed value 100 and output quantities 2 and 3 yielded output values 100 and 100, total 200. The output onchange repeats the same allocation logic using product standard prices. No Odoo valuation/posting executed.
- **Impact:** Produced inventory can be valued above consumed cost, overstating output costs and subsequent margins/stock valuation.
- **Suggested fix:** Define a cost allocation policy across outputs and distribute the total once, preserving summed output value and handling quantity/unit differences explicitly.
- **Validation needed:** One/multiple outputs, different quantities/units, rounding and zero quantities; output allocation total must equal the intended consumed cost.

## SIMPLE-002 — P1: Confirm can create duplicate transfers after production is done

- **Status:** Fixed in 19.0.1.1.3. `do_transfer()` starts with `_check_can_transfer()`: row lock (`SELECT ... FOR UPDATE`), then refuses a record not in draft or already linked to transfers. Covered by `test_confirm_only_once`.
- **Location:** models/mrp_simple.py, do_transfer(); views/mrp_simple_view.xml.
- **Trigger:** Call do_transfer again on a done record through ORM/RPC or another server-side caller.
- **Actual behavior:** Only the form hides Confirm after draft. The method has no draft-state check or existing-transfer guard. It creates new receipt/consumption pickings, optionally creates another sale/output line, overwrites consume_id/receipt_id and validates according to the flags.
- **Evidence:** Complete method and UI inspected. New stock.picking creation occurs unconditionally before any workflow check; no server-state constraint exists. No real repeated transfer executed.
- **Impact:** Repeated confirmation can consume/produce stock twice and lose the original transfer links on the production record; automatic sale creation can also be duplicated.
- **Suggested fix:** Enforce draft-only confirmation on the server and protect against existing linked transfers/repeated requests; provide a separately validated correction workflow if needed.
- **Validation needed:** Second call on done must create no extra pickings/moves/sales; concurrent or retried calls must preserve one confirmation.

## SIMPLE-003 — P1: Received products are valued at their own cost, not at the consumed cost

- **Status:** Fixed in 19.0.1.1.4. The receipt moves carry `mrp_simple_id`; `stock.move._get_value_from_production()` values them at the move `price_unit` (converted to the product unit), the allocated cost. Moves merged in `add_picking_line()` keep the weighted average price. Covered by `test_receipt_valued_at_consumed_cost`, `test_merged_receipt_lines_keep_weighted_price`.
- **Location:** models/mrp_simple.py, add_picking_line() and create_picking_lines_in().
- **Trigger:** Confirm a simple production whose received product has a cost different from the allocated price.
- **Actual behavior:** In Odoo 19 `stock_account` does not use `stock.move.price_unit` for valuation; without a bill, purchase line, return or manufacturing order the move falls back to `standard_price x quantity`. Consumed 70, received 2 units with cost 100: receipt value 200 instead of 70.
- **Impact:** Stock value and average cost of the produced goods are wrong, without any error; the difference reaches the accounting.

## Review limitations

All eligible Python/XML module source manually reviewed, including transfer creation/validation, stock move aggregation, sale generation, cost calculations, multi-line wizard, ACLs and views. Cost reproduction uses mocked records; no Odoo transfers, sales, valuation entries or database integration tests executed.
