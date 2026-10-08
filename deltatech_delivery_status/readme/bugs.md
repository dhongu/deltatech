# Bug review — Delivery Status

Review date: 2026-10-02. Target version: Odoo 19.

## DELIVERYSTATUS-001 — P2: Postponed-delivery search rejects normalized boolean operators

- **Status:** Not reproduced (2026-10-08). Odoo 19 retries a search method that refuses `in` / `not in` with `=` / `!=` for each value (`DomainCondition._optimize_field_search_method()`), so `[("postponed_delivery", "in", [True])]` works with the current hook. Covered by `test_search_postponed_delivery_in_operators`, which passes on the original code.
- **Location:** models/sale.py, _search_postponed_delivery().
- **Trigger:** Use the provided Postponed delivery order filter or any domain on the nonstored postponed_delivery Boolean.
- **Actual behavior:** The search method accepts only =/!= and a Boolean scalar. Odoo 19 normalizes Boolean comparisons to in/not in with [True] before custom search evaluation, so the hook raises NotImplementedError instead of returning a domain.
- **Evidence:** Compared local ORM Boolean domain normalization with this hook; executed the actual AST-extracted hook with in/[True], reproducing NotImplementedError. No database search or browser filter executed.
- **Impact:** The order filter added by this module cannot reliably retrieve postponed deliveries; equality/negative forms face the same normalization incompatibility.
- **Suggested fix:** Support Odoo 19 in/not in Boolean collections with correct positive/negative semantics, including empty/all-value domains, or return NotImplemented for unsupported shapes as appropriate.
- **Validation needed:** Provided UI filter and direct searches for True/False, =/!= and in/not in, orders with mixed postponed pickings and no pickings.

## DELIVERYSTATUS-002 — P1: Confirmation postpones delivery even after its payment is done

- **Status:** Fixed in 19.0.2.3.3. `_action_confirm()` postpones only when the last transaction is not `done`. Covered by `test_paid_quotation_is_not_postponed_on_confirmation` and `test_pending_payment_postpones_on_confirmation`.
- **Location:** models/sale.py, _action_confirm(); models/payment_transaction.py, _set_done().
- **Trigger:** A provider has postponed_delivery enabled; payment completes while the linked sale order is still a quotation, then native payment post-processing confirms it.
- **Actual behavior:** _set_done tries to release only orders already reporting postponed_delivery. A quotation without transfers is not postponed. Later _action_confirm creates transfers and unconditionally postpones them when the selected provider has the flag, without checking transaction state. The already-completed transaction does not transition to done again to release those new transfers. The team wire-transfer branch also ignores completed payment state.
- **Evidence:** Executed actual AST-extracted order confirmation with transaction.state=done and flagged provider: postpone_delivery is still called. Read native sale payment _post_process and _check_amount_and_confirm_order: done transactions subsequently call quotation.action_confirm. No payment, order or stock mutation executed.
- **Impact:** Fully paid orders can retain postponed transfers, and button_validate refuses them until an operator manually releases delivery.
- **Suggested fix:** Postpone only when the relevant payment condition remains outstanding; reconcile delivery state after confirmation/payment post-processing with explicit handling of done/authorized/partial payments and team transfer settings.
- **Validation needed:** Payment completed before/after quotation confirmation, provider/team flags, partial and authorized payments, and creation of transfers after completion; paid eligible deliveries must not stay blocked.

## Review limitations

All eligible Python/XML files, including legacy/current migrations, were manually read. Reproductions use AST-extracted methods with mock orders/transactions. No Odoo integration tests, translation migration, real payment or stock operation executed.
