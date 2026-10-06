# Bug review — eCommerce Sale Order Status

Review date: 2026-10-02. Target version: Odoo 19.

## WEBSTATUS-001 — P2: Sent website orders lose the Placed stage

- **Status:** Open.
- **Location:** models/sale.py, _compute_stage().
- **Trigger:** A website quotation reaches state sent.
- **Actual behavior:** The first if assigns placed, but the separate draft/cancel if chain executes its else and immediately replaces it with in_process.
- **Evidence:** The actual AST-extracted compute returned in_process for state=sent, website_id=True, no postponement.
- **Impact:** The Placed filters and portal quotation badge misclassify newly submitted website orders.
- **Suggested fix:** Use one mutually exclusive state chain; preserve the placed assignment.
- **Validation needed:** Website sent/draft/cancel and nonwebsite quotations, including postponement.

## WEBSTATUS-002 — P2: Completed stock transfers overwrite carrier delivery status

- **Status:** Open.
- **Location:** models/sale.py, _compute_stage(); models/stock_picking.py, write().
- **Trigger:** A confirmed order has a completed stock transfer whose carrier status is in_transit.
- **Actual behavior:** The compute initially assigns in_delivery, then unconditionally assigns delivered when all stock transfers are done or canceled. The dependency on delivery_state recomputes this field after the picking write override assigns an intermediate carrier stage. All canceled transfers are also classified as delivered.
- **Evidence:** Actual AST compute with state=sale and one picking state=done/delivery_state=in_transit returned delivered. A separate all-canceled transfer case also returned delivered. The dependency module explicitly distinguishes carrier status from stock state.
- **Impact:** Customers and operators see delivery completion while the parcel is still with the carrier, and canceled fulfillment can appear successful.
- **Suggested fix:** Derive carrier completion from delivery_state and distinguish canceled fulfillment from actual delivery; do not overwrite intermediate carrier stages using stock state alone.
- **Validation needed:** Completed stock transfers with each carrier state, multiple parcels, canceled transfers and partial deliveries without backorders.

## WEBSTATUS-003 — P2: Portal cancellation filters use an invalid stage value

- **Status:** Open.
- **Location:** controllers/portal.py, _prepare_portal_layout_values() and _prepare_orders_domain().
- **Trigger:** A canceled order is viewed through the Canceled, Open Orders or Closed Orders portal filter.
- **Actual behavior:** The order compute assigns canceled, while both portal filter dictionaries and applied domains use cancel. Canceled-stage records never match the cancellation filter, remain in the open-stage domain and are excluded from the closed-stage domain.
- **Evidence:** Executed actual AST-extracted domain method: cancel generated stage = cancel, open_order excluded only delivered/cancel, closed_order included only delivered/cancel. The declared selection and compute use canceled. Native sale portal retains its own base access/state domain.
- **Impact:** Cancellation filtering is incorrect wherever the base portal domain admits those records; the stage filter cannot select the value actually stored.
- **Suggested fix:** Use canceled consistently in both displayed filter domains and applied search domains.
- **Validation needed:** Canceled-stage records admitted by the base domain, open/closed/canceled filters and portal access isolation.

## Review limitations

All eligible Python/XML source was read. Isolated executions used AST-extracted methods and mock records; no Odoo database, portal HTTP or carrier integration tests were executed.
