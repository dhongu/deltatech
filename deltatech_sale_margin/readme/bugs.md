# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## MARGIN-001 — P2: Blocking margin validation ignores incompatible-unit protection

- **Status:** Fixed in 19.0.1.2.1 — `check_sale_price()` and `change_price_or_product()` now call `_margin_uom_comparable()` and skip the cost/margin comparison for incompatible unit families, the same policy as `_margin_for_check()`. Covered by tests in `tests/test_margin_check_mode.py` (write, confirmation with check-on-validate, onchange, and a same-family packaging unit that must still block). The "no price" check still applies to such lines. Priority P2 confirmed.
- **Location:** models/sale.py, _margin_for_check(), change_price_or_product(), and check_sale_price().
- **Trigger:** A product base UoM and sale-line UoM have different roots, causing the native cost conversion to inflate purchase_price; use margin check mode block.
- **Actual behavior:** The warning compute deliberately returns no margin for incompatible units, but the onchange and blocking validation compare price and purchase_price directly without calling _margin_uom_comparable(). The same line can show no below-limit flag and still be blocked by the inflated cost.
- **Evidence:** Executed existing methods with price 100, converted cost 1000 and unit compatibility False: _margin_for_check() returned None, while check_sale_price() raised the below-purchase-price error.
- **Impact:** Sales are blocked by comparisons the module itself identifies as invalid; warning and enforcement disagree.
- **Suggested fix:** Apply the same comparability policy in warnings and enforcement, or reject inconsistent UoM setup with an explicit configuration error before comparing costs.
- **Validation needed:** Compatible Unit/Dozen units, incompatible roots, block/warn/off modes, positive margin limits, and users with override groups.

## MARGIN-002 — P2: No-change-price role is enforced only by view readonly

- **Status:** Open.
- **Location:** models/sale.py, _compute_can_change_price()/SaleOrderLine.write(); views/sale_margin_view.xml, view_order_form_no_change_price.
- **Trigger:** A salesperson assigned group_sale_no_change_price writes a sale line price_unit or discount via ORM/RPC, with the resulting price still above the cost/margin threshold.
- **Actual behavior:** The group only determines can_change_price for readonly modifiers on the form/list. The line write override checks below-cost/margin policy but never checks this group's restriction on changing price/discount. No create guard or field-level group restriction enforces it either.
- **Evidence:** Complete module model/security/view source inspected. Group membership is checked only in can_change_price; public ORM writes follow the normal sale-line ACL and margin checks. No live price mutation executed.
- **Impact:** Users explicitly assigned the no-price-change role can alter commercial prices or discounts through another client or RPC despite the restriction shown in the UI.
- **Suggested fix:** Enforce price/discount modification permissions server-side, covering direct line writes and order one2many commands while allowing validated automatic price computation paths.
- **Validation needed:** Restricted salesperson direct writes/one2many commands, discounts and prices above/below cost, ordinary salesperson and authorized automatic repricing; UI and server permissions must agree.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run during the review. MARGIN-001 was fixed afterwards (2026-10-01) with database-backed tests.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **MARGIN-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.
