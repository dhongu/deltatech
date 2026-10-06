# Confirmed bugs — 2026-10-03

## PROJECTPRICE-001 — P2: direct create overrides explicit context pricelist

`models/sale_order.py:46–68` checks only vals.pricelist_id before assigning the project pricelist. It ignores context.default_pricelist_id, although default_get explicitly preserves it (:16–17) and the project action also preserves upstream defaults. Calling create without a pricelist in vals, with create_for_project_id=P and default_pricelist_id=A, writes project listB into vals before native default application. Core _add_missing_default_values fills only missing fields, so A never applies. Respect explicit context defaults before injecting the project list to make direct creation agree with the form/default-get path.

Evidence: entire module source traced through native ORM create/_add_missing_default_values and sale_project default_get. Source-supported precedence mismatch; programmatic/database creation not executed. Existing explicit vals.pricelist_id remains respected.

## Limits

All eligible source reviewed against native project.action_view_sos, action context dictionaries and project views. Project pricelist field lacks company domain/check_company while sale order pricelist enforces it; foreign-company selections require a database configuration/creation test before an additional finding is asserted. No project/task/sales/browser tests executed.
