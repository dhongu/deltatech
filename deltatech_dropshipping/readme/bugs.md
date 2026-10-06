# Confirmed bugs — 2026-10-03

## DROPPRICE-001 — P2: loss warning compares incompatible prices and ignores discounts

`models/purchase_order.py:23–47` removes taxes from raw price_unit using each order's currency, then compares the numbers without currency/UoM conversion or line discounts. Purchase40 RON versus sale10 EUR (rate5) wrongly warns; purchase120 per dozen versus sale15 per unit also wrongly warns. Purchase80 versus sale100 with a 50% sale discount misses the loss. Native purchase/sale prices have independent product_uom_id, currency and discount; normalize discounted untaxed prices to a common unit and currency/date before comparing. Include those mutable inputs in compute dependencies as well.

Evidence: original compute executed with isolated tax/line doubles, showing false positives and absent warning. Native unit/discount fields and price-normalization helpers inspected. Fixture `audit_coverage/reproductions/dropshipping_price_warning.py` models tax removal only; hypothetical currency rates/unit factors/net discounts supply expected comparisons, not native currency/tax computation. No purchase/sale database scenario executed.

## Limits

Entire eligible source read; native stock_dropshipping transitive sale_stock provider and picking.sale_id relation traced. Shipping address compute lacks explicit dependency decorators; cache/UI refresh after relation edits remains a validation limitation, not a separately reproduced finding. HTML sanitation and translation paths reviewed without a browser run.
