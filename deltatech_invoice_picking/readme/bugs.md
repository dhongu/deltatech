# Bug review — Invoice Pickings

Review date: 2026-10-02. Target version: Odoo 19.

## PICKINV-001 — P1: Picking quantities are copied into invoice units without conversion

- **Status:** Fixed in 19.0.1.0.12 — `purchase.order.line._prepare_account_move_line()` and `sale.order.line._prepare_invoice_line()` convert each move quantity from `move.product_uom` to the order line `product_uom_id` (HALF-UP, as the core delivered/received computations) before summing and before the sale remaining-quantity cap. Covered by tests in tests/test_invoice_picking_uom.py.
- **Location:** models/purchase.py, _prepare_account_move_line(); models/sale.py, _prepare_invoice_line().
- **Trigger:** An order/invoice unit differs from the selected stock move unit.
- **Actual behavior:** Both overrides sum move.quantity directly but keep the superclass product_uom_id and price_unit. The sale cap compares numbers in different units rather than converting them.
- **Evidence:** Executed the actual extracted methods with mock records: 12 received units yield quantity 12 in an invoice unit of dozen, at 120 per dozen; one delivered dozen yields quantity 1 in an invoice unit of unit when 24 units remain invoiceable. Local stock.move._compute_quantity expresses quantity in product_uom; core sale/purchase stock delivery computations convert it to the order unit.
- **Impact:** Bills may charge 12 times the correct amount; customer invoices may omit delivered quantities. The numerical cap does not restore unit compatibility.
- **Suggested fix:** Convert every signed move quantity from move.product_uom to the invoice/order product_uom_id before summing or applying remaining-quantity limits.
- **Validation needed:** Unit/Dozen and kg/g, partial transfers, returns and mixed move units; assert both physical quantity and monetary total.

## PICKINV-002 — P2: Picking billing status is decided by one invoice line instead of cumulative coverage

- **Status:** Open.
- **Location:** models/account_move.py, update_pickings().
- **Trigger:** A normal order invoice covers several products in one picking only partially, or the same delivered quantity is invoiced across several invoices.
- **Actual behavior:** Each line overwrites the whole picking to_invoice flag using only its own quantity versus one stock move. A full line can clear an earlier partial line; once cleared, later lines are skipped. Prior invoices are not accumulated.
- **Evidence:** Executed the actual extracted method with mock records. Product A invoiced 5/10 followed by product B 10/10 leaves to_invoice=False. Two invoices each for 5 against a delivery of 10 leave to_invoice=True after both invoices. No Odoo database executed.
- **Impact:** The To invoice filter/button can hide transfers with unbilled products or continue showing fully billed transfers. Results depend on invoice line ordering.
- **Suggested fix:** Calculate signed cumulative invoiced quantities in compatible units per delivered order line, then derive the picking flag once from all relevant moves; preserve invoice-to-picking allocation explicitly.
- **Validation needed:** Multiple products in both line orders, sequential partial invoices, refunds, cancellations and multiple pickings per order line.

## PICKINV-003 — P2: Batch invoicing excludes pickings that still need partial billing

- **Status:** Open.
- **Location:** models/stock_picking_batch.py, _compute_invoiced()/action_create_invoice().
- **Trigger:** A done batch contains a picking with account_move_id set and to_invoice=True after a partial order invoice.
- **Actual behavior:** The batch compute treats any invoice link as fully invoiced. The action removes all linked pickings without checking to_invoice, and so omits partially billed pickings from the invoice wizard or supplier bill selection.
- **Evidence:** Complete batch source read. Both incoming and outgoing branches filter solely on account_move_id; neither checks the remaining-billing flag. The account update method explicitly supports a linked picking with to_invoice=True.
- **Impact:** Remaining products/quantities cannot be invoiced through the batch action, and the batch can be reported as invoiced prematurely.
- **Suggested fix:** Derive batch invoiced state from remaining billable coverage and retain partially invoiced pickings in the action; aggregate selected quantities safely.
- **Validation needed:** Outgoing/incoming batches containing fully billed, partially billed and unbilled pickings; verify remaining lines are selectable once.

## PICKINV-004 — P1: Supplier invoice action can bill the same receipt repeatedly

- **Status:** Fixed in 19.0.1.0.14. `purchase.order.line._prepare_account_move_line()` caps the receipt quantity at the native remaining quantity to bill (received − billed on non-cancelled bills), as the sale flow caps at the remaining quantity to invoice, and `stock.picking.action_create_supplier_invoice()` refuses receipts whose order lines have nothing left to bill, so no empty bill is created and the existing invoice link is kept. A cancelled bill frees the quantity again. Covered by tests in tests/test_invoice_picking_double_bill.py.
- **Location:** models/stock_picking.py, action_create_supplier_invoice(); models/purchase.py, _prepare_account_move_line().
- **Trigger:** Run the bound Create Purchase Invoices list action again for an already billed done receipt with a supplier invoice number.
- **Actual behavior:** The action checks state and invoice number but not account_move_id, to_invoice or previous billed quantities. The preparation override replaces the native remaining quantity with the entire selected receipt quantity even when the remaining quantity is zero. The account create hook then replaces the old receipt invoice link with the new bill.
- **Evidence:** Executed the actual extracted purchase preparation method with native pending quantity zero and a selected receipt quantity one: it returns quantity one. Read local Odoo 19 purchase.order.action_create_invoice in full: it calls preparation for order lines and creates bills without a qty_to_invoice guard. The module binds the list server action, so hiding the form button does not prevent repeated execution. No live duplicate bill created.
- **Impact:** An already billed receipt can generate another nonzero draft vendor bill and overwrite its invoice association. Posting that bill can duplicate payable/accounting amounts.
- **Suggested fix:** Enforce remaining receipt-specific signed billable quantity server-side, reject already fully billed receipts, and maintain allocations across bills/refunds instead of a single replaceable link.
- **Validation needed:** Repeated list action, mixed billed/unbilled receipts, partial bills, cancellations and returns; total billed physical quantity must never exceed remaining eligible receipts.

## Review limitations

All eligible Python/XML source was read. Isolated AST-extracted method reproductions use mock objects and do not establish Odoo integration coverage. No database billing, posting, migrations or runtime tests were executed.
