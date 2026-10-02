# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## REORDER-001 — P1: Automatic rules use the default user company instead of the active company

- **Status:** Open.
- **Location:** `models/product.py:10–41, create_rule()`.
- **Trigger:** A user whose default company is A switches to company B and creates a product; both companies are allowed and A has an enabled warehouse.
- **Actual behavior / impact:** Warehouse and existing-rule searches use env.user.company_id. The generated values omit company_id, whose core default is env.company. This mixes an A location with company B and can fail the core company consistency check or skip the intended B rule.
- **Evidence:** Executed the extracted method with default company 1 and active company 2: it selected location 11 belonging to company 1 and emitted no company_id. Core stock.warehouse.orderpoint defaults company_id to env.company and enables automatic company checks.
- **Suggested fix:** Use the active/document company consistently for warehouses, routes, existing rules and creation values.
- **Validation needed:** Create products in B while the user defaults to A; assert all generated rules and locations belong to B.

## REORDER-002 — P2: One existing rule prevents generation for other warehouses

- **Status:** Open.
- **Location:** `models/product.py:23–41, create_rule()`.
- **Trigger:** A product already has a rule in warehouse W1; enable automatic rules in W2 and invoke Create rule.
- **Actual behavior / impact:** The existing-rule search is scoped only by product and company. Any matching rule skips the entire warehouse loop, so W2 never receives its missing rule.
- **Evidence:** Executed the extracted method with two enabled warehouses and one existing rule: no new rule was emitted. The core uniqueness key is product_id, location_id, company_id.
- **Suggested fix:** Check existence for each target location and company, preserving existing rules.
- **Validation needed:** With a rule at W1 only, generate W2 and repeat the action without duplicates.

## REORDER-003 — P2: The string False disables automatic rule creation

- **Status:** Open.
- **Location:** `models/product.py:53–62, create()`.
- **Trigger:** Set deltatech_auto_reorder_rule.dont_auto_create_rule to False in System Parameters.
- **Actual behavior / impact:** get_param returns the stored string. The code checks its Python truthiness, so the non-empty string False disables generation exactly like True.
- **Evidence:** Confirmed get_param returns stored text; evaluated the same condition with False as text, which is truthy.
- **Suggested fix:** Parse the setting with tools.str2bool rather than string truthiness.
- **Validation needed:** Check missing, False, 0 and True values; only enabled values should disable auto creation.

## REORDER-004 — P1: The location wizard creates rules with a removed field

- **Status:** Fixed in 19.0.0.1.5 — `do_create()` no longer sends the obsolete `qty_multiple` key (always 0, absent from `stock.warehouse.orderpoint` in Odoo 19; it only exists when the optional `deltatech_stock_orderpoint_multiple` is installed). Covered by tests in `tests/test_order_rules_wizard.py` (wizard creates the rule with product, location, min/max and trigger).
- **Location:** `wizard/order_rules_details.py:17–42, do_create()`.
- **Trigger:** Open Rules Wizard on a product, choose at least one location and create rules.
- **Actual behavior / impact:** Every generated dictionary contains qty_multiple. The stock.warehouse.orderpoint model supplied by the declared dependencies has no such field in Odoo 19; ORM creation rejects it with Invalid field qty_multiple.
- **Evidence:** Executed the extracted wizard with one variant and one location: the emitted dictionary contains qty_multiple. Compared the local Odoo 19 model, which uses replenishment_uom_id, and ORM invalid-field validation.
- **Suggested fix:** Remove the obsolete zero-valued field; use the Odoo 19 replenishment unit API if a multiple is needed.
- **Validation needed:** Install only the declared dependencies and save the wizard; verify product, location, min/max and trigger.

## Review limitations

Source inspection and isolated executions with mocked records; no database-backed module installation or integration tests were run in this pass.
