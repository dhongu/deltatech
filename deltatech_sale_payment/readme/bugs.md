# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## SALEPAY-001 — P1: Partial foreign-currency payments can mark orders fully paid

- **Status:** Fixed in 19.0.1.2.2. `_compute_payment` takes the invoice side from `amount_total - amount_residual` in the invoice currency (negative for credit notes) instead of the `*_signed` company-currency amounts; invoices and transactions in a currency other than the order's are converted at the document date (`_payment_to_order_currency`). The max(invoice, transactions) deduplication policy is unchanged. The SQL of the 19.0.1.2.0 migration uses the invoice currency too, and the 19.0.1.2.2 post-migration recomputes the orders in a foreign currency. Tests: `TestSaleOrderPaymentForeignCurrency` (partial and full payment of a EUR order in a USD company at rate 5, full credit note); the partial case failed before the fix with 250 instead of 50.
- **Priority:** P1 kept: it affects only orders in a currency other than the company's, but there it shows `done` and the payment link proposes 0.
- **Location:** models/sale.py, _compute_payment(), lines 59–91.
- **Trigger:** Create a EUR 100 order in a RON company, invoice it at 5 RON/EUR, and reconcile EUR 50 without a completed payment transaction.
- **Actual behavior:** The computation mixes invoice amounts in company currency with transaction amounts and order totals in order currency. It records 250 as the amount paid and sets payment_status to done instead of recording EUR 50 as partial.
- **Evidence:** Executed the existing method extracted from its AST against minimal records: signed invoice total 500, residual 250, order total 100, no transactions; result payment_amount=250 and payment_status=done.
- **Impact:** Payment status and remaining-payment calculations can incorrectly indicate that no further payment is due.
- **Suggested fix:** Normalize all sources into the order currency using an explicit conversion date and preserve the intended invoice/transaction deduplication policy.
- **Validation needed:** Partial and full payments in both currency directions, exchange-rate changes, refunds, and transaction/invoice overlap.

## SALEPAY-002 — P2: "Confirm Payment" date is never stored

- **Status:** Fixed in 19.0.1.3.0. The date goes in the transaction's `state_message`, in a note on the order and, through the `payment_date` context read by `_create_payment`, as the date of the accounting payment; `do_confirm` post-processes the transaction right away. Tests: `test_confirm_records_payment_date`, `test_confirm_dates_the_accounting_payment`. Found while writing the consultant sheet (2026-10-01).
- **Location:** wizard/sale_confirm_payment.py, do_confirm().
- **Actual behavior:** `payment_date` is only passed as `with_context(payment_date=...)`; nothing reads it, so the date shown in the wizard is lost.

## SALEPAY-003 — P1: "Confirm Payment" deletes a done or authorized transaction

- **Status:** Fixed in 19.0.1.3.0. `default_get` takes over only a draft or pending transaction and otherwise proposes the rest to pay; `update_transaction` raises instead of cancelling and deleting; an order with an authorized transaction is refused. Tests: `test_done_transaction_is_not_replaced`, `test_update_refuses_a_confirmed_transaction`, `test_authorized_transaction_is_refused`; `test_wizard_update_transaction` asserted the deletion and now asserts the refusal.
- **Location:** wizard/sale_confirm_payment.py, default_get() and update_transaction().
- **Actual behavior:** the `and`/`or` precedence in default_get picks up the last transaction also when it is `done` or `authorized`; update_transaction then calls `_set_canceled()` (no effect on `done`) and `unlink()`, and do_add_payment creates a new one. On an electronic provider the accounting payment of the old transaction remains and post-processing creates a second one.

## SALEPAY-004 — P2: a salesman without Invoicing rights cannot confirm

- **Status:** Fixed in 19.0.1.3.0 with a controlled sudo: the wizard checks `check_access("write")` on the order, then writes the transaction as superuser (`create_uid` stays the user). Salesmen get read access on `payment.transaction` (the `sale` record rule already lets them see every transaction) and the action is restricted to `sales_team.group_sale_salesman`. Tests: `test_salesman_without_invoicing_can_confirm` (`new_test_user` with sales rights only), `test_salesman_cannot_confirm_others_orders`.
- **Actual behavior:** `payment.transaction` is accessible only to `account.group_account_invoice` (no unlink) and `base.group_system`; the wizard writes without sudo, so a sales-only user gets an access error on Confirm and Add.

## SALEPAY-005 — P2: confirmed wire-transfer transactions fail post-processing for 4 days

- **Status:** Fixed in 19.0.1.3.0. `payment.transaction._create_payment` returns no payment when the provider's journal has no inbound payment method line for it, so the post-processing goes on (quotation confirmation, automatic invoice) and the transaction is flagged as post-processed. Tests: `test_post_processing_without_payment_method_line` (provider `none`), `test_wire_transfer_provider` (`payment_custom`, skipped when it is not installed).
- **Actual behavior:** Odoo 19 has no `account.payment.method` for the `custom` provider code, so after the wizard sets a wire-transfer transaction `done`, `_post_process` raises "Please define a payment method line on your payment." in `_create_payment`. The cron rolls back (order not confirmed, no invoice, no payment) and retries every 10 minutes for 4 days.

## SALEPAY-006 — P1: Public transaction update bypasses order access and ownership checks

- **Status:** Fixed in 19.0.1.3.2 — `update_transaction` became the private `_update_transaction` (no longer callable through RPC), which checks write access on the order itself. Every entry point (`do_add_payment`, `do_confirm`, `_update_transaction`) calls `_check_payment_values()` before the superuser write: the transaction must belong to the order checked by `_get_order()`, the provider must be of the order's company, and the payment method must be one of the provider's (or the generic "unknown" method). Covered by tests in `tests/test_confirm_payment.py` (`test_update_transaction_is_not_callable_remotely`, `test_transaction_of_another_order_is_refused`, `test_private_update_checks_the_order`, `test_provider_of_another_company_is_refused`, `test_payment_method_of_another_provider_is_refused`).
- **Location:** wizard/sale_confirm_payment.py, update_transaction(); security/ir.model.access.csv.
- **Trigger:** An internal user creates their own wizard with a chosen pending/draft transaction_id and calls update_transaction directly through ORM/RPC, or supplies an unrelated transaction on a wizard for an accessible order.
- **Actual behavior:** update_transaction is public and immediately sudo-reads/writes the selected transaction. It does not call _get_order, check caller transaction write access or verify membership in the order's transaction_ids. The parent actions check order write access but likewise do not bind transaction_id to that order. Wizard ACL grants all internal users create/write; transaction_id readonly only affects UI.
- **Evidence:** Executed the actual method extracted by AST with a mocked pending transaction and no order/access objects. It performed a privileged write of amount=99, provider_id=2 and payment_method_id=3 without any access/ownership check. No actual payment or RPC executed.
- **Impact:** A user lacking accounting transaction write rights can alter another order's pending payment amount/provider/method, including a transaction outside the intended order/company scope. An unrelated transaction can also be confirmed through the parent flow after an accessible-order check.
- **Suggested fix:** Enforce caller order access and transaction-to-order/company membership inside every public mutation entry point before sudo; validate provider/method compatibility and amount there as well.
- **Validation needed:** Direct update RPC from an internal user, another salesperson's transaction, unrelated-company transaction, accessible order with mismatched transaction, and the normal authorized payment workflow.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run at review time. SALEPAY-001 to SALEPAY-005 were fixed on 2026-10-01 with database-backed tests.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **SALEPAY-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.
