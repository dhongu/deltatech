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

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run during the review. MARGIN-001 was fixed afterwards (2026-10-01) with database-backed tests.
