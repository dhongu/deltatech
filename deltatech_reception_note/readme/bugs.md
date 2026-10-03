# Bug review — deltatech_reception_note

Review date: 2026-10-02. Target version: Odoo 19.

## RECEPTION-001 — P2: RFQ consumption ignores differing purchase units

- **Status:** Open.
- **Location:** models/purchase.py, reduce_from_rfq().
- **Trigger:** Reception-note and sent-RFQ lines for the same product use different units.
- **Actual behavior:** The method compares/subtracts raw product_qty and writes the raw remainder to each RFQ without converting between product_uom_id values.
- **Evidence:** Full reduction source read; no _compute_quantity exists in matching/comparison/decrement paths. A note for one dozen against an RFQ for twelve pieces consumes one RFQ piece, leaving eleven instead of zero. Source arithmetic evidence only.
- **Impact:** Remaining RFQ demand and forced-excess messages represent the wrong physical quantity.
- **Suggested fix:** Convert quantities into a common product unit for validation and each RFQ unit when decrementing; use unit rounding.
- **Validation needed:** Unit/Dozen and kg/g, several RFQs with different units, multiple note lines and forced excess.

## RECEPTION-002 — P1: Reception notes consume sent RFQs from other allowed companies

- **Status:** Fixed in 19.0.0.1.4 — `reduce_from_rfq()` adds `("company_id", "=", self.company_id.id)` to the RFQ search and `button_confirm()` calls it with `with_company(order.company_id)`. Covered by tests in tests/test_reception_note_company.py.
- **Location:** models/purchase.py, reduce_from_rfq().
- **Trigger:** Two allowed companies have sent rfq_only orders for the same supplier/product, and a note belongs to one company.
- **Actual behavior:** RFQ search uses supplier, type, state and is_empty only; it does not restrict company_id. Matching product quantities are then decremented from all returned RFQs, ordered by date.
- **Evidence:** Actual AST-extracted method records the RFQ search domain without company_id for a mock note in company 2. Full mutation loop confirms returned lines are written. No actual RFQ modified.
- **Impact:** A receipt in one company can reduce another company demand and mark its RFQ empty, corrupting company-specific purchase planning.
- **Suggested fix:** Restrict RFQ matching to the note company and perform reduction in its company context.
- **Validation needed:** Same supplier/product in two allowed companies, older foreign-company RFQ first, and one-company access; only the note company may be decremented.

## RECEPTION-003 — P2: Confirming an already confirmed note consumes RFQ demand again

- **Status:** Open.
- **Location:** models/purchase.py, button_confirm()/reduce_from_rfq().
- **Trigger:** Call button_confirm again on a reception_type=note order already in purchase state, through ORM or another client.
- **Actual behavior:** Native confirmation skips orders outside draft/sent. This override still loops over every original order after super and invokes reduce_from_rfq, regardless of whether confirmation occurred or demand was previously consumed.
- **Evidence:** Compared complete override with local native purchase.order.button_confirm, which continues for state not in draft/sent. The custom post-super loop has no state/idempotency marker and writes RFQ remainders each time. No repeated live confirmation executed.
- **Impact:** Repeated confirmation subtracts the same receipt quantity again or raises excess-quantity errors after an otherwise successful earlier confirmation.
- **Suggested fix:** Limit reduction to orders actually undergoing their first successful confirmation and persist allocation/idempotency state where needed.
- **Validation needed:** Confirm once/twice, RPC on purchase/cancel states, approval workflow and mixed recordsets; demand must be consumed exactly once.

## RECEPTION-004 — P1: Conversion wizard copies prices without the source order currency

- **Status:** Fixed in 19.0.0.1.4 — `do_create_reception_note()` creates the RFQ-only order with `with_company(purchase.company_id)` and passes the source `company_id`, `currency_id` and `fiscal_position_id`, so the copied prices and taxes keep their basis. Covered by tests in tests/test_reception_note_company.py.
- **Location:** wizard/reception_note.py, do_create_reception_note().
- **Trigger:** Create the RFQ-only counterpart from a normal purchase order in a currency other than the new order default.
- **Actual behavior:** New header values omit currency_id/company_id, but line price_unit and taxes are copied without currency conversion. The new order uses its defaults; the currency of its numerical prices is lost.
- **Evidence:** Actual AST-extracted wizard executed with source currency_id=99: captured create header has no currency_id or company_id. Full line loop copies price_unit unchanged. Mock header only; no currency/order mutation executed.
- **Impact:** The resulting RFQ can represent an incorrect monetary amount and price basis. A source company differing from the environment can additionally conflict with the copied picking type company.
- **Suggested fix:** Preserve the source company/currency explicitly along with relevant commercial defaults, or perform deliberate dated price conversion if changing currency.
- **Validation needed:** Foreign-currency source order, same/different active company and remaining partially received lines; verify currency, unit prices, taxes and company consistency.

## Review limitations

All eligible Python/XML source was read. AST-extracted search/wizard methods use mock objects. No Odoo receipt/order/RFQ mutation, confirmation or integration test executed.
