# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## SIMPLE-001 — P1: Multiple output lines each receive the entire consumed cost

- **Status:** Open.
- **Location:** models/mrp_simple.py, compute_finit_price() and MRPSimpleLineIn.compute_finit_price().
- **Trigger:** Produce two or more output lines and recompute their prices, or change an output quantity in the form.
- **Actual behavior:** The full input cost is divided by each output line quantity independently. Therefore each output line has a value equal to the complete input cost; summed output value multiplies cost by the number of output lines.
- **Evidence:** Executed the actual parent recomputation method extracted by AST: consumed value 100 and output quantities 2 and 3 yielded output values 100 and 100, total 200. The output onchange repeats the same allocation logic using product standard prices. No Odoo valuation/posting executed.
- **Impact:** Produced inventory can be valued above consumed cost, overstating output costs and subsequent margins/stock valuation.
- **Suggested fix:** Define a cost allocation policy across outputs and distribute the total once, preserving summed output value and handling quantity/unit differences explicitly.
- **Validation needed:** One/multiple outputs, different quantities/units, rounding and zero quantities; output allocation total must equal the intended consumed cost.

## SIMPLE-002 — P1: Confirm can create duplicate transfers after production is done

- **Status:** Open.
- **Location:** models/mrp_simple.py, do_transfer(); views/mrp_simple_view.xml.
- **Trigger:** Call do_transfer again on a done record through ORM/RPC or another server-side caller.
- **Actual behavior:** Only the form hides Confirm after draft. The method has no draft-state check or existing-transfer guard. It creates new receipt/consumption pickings, optionally creates another sale/output line, overwrites consume_id/receipt_id and validates according to the flags.
- **Evidence:** Complete method and UI inspected. New stock.picking creation occurs unconditionally before any workflow check; no server-state constraint exists. No real repeated transfer executed.
- **Impact:** Repeated confirmation can consume/produce stock twice and lose the original transfer links on the production record; automatic sale creation can also be duplicated.
- **Suggested fix:** Enforce draft-only confirmation on the server and protect against existing linked transfers/repeated requests; provide a separately validated correction workflow if needed.
- **Validation needed:** Second call on done must create no extra pickings/moves/sales; concurrent or retried calls must preserve one confirmation.

## Review limitations

All eligible Python/XML module source manually reviewed, including transfer creation/validation, stock move aggregation, sale generation, cost calculations, multi-line wizard, ACLs and views. Cost reproduction uses mocked records; no Odoo transfers, sales, valuation entries or database integration tests executed.
