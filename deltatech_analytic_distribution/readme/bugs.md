# Bug review — Analytic Distribution Enforcer

Review date: 2026-10-02. Target version: Odoo 19.

## ANALYTICENFORCE-001 — P1: Posting multiple bills reads a singleton field on the whole batch

- **Status:** Fixed in 19.0.0.0.4 — `action_post()` filters the vendor documents (in_invoice/in_refund/in_receipt) of the batch and validates each one, instead of reading `self.move_type` on the whole recordset. The company switch is still read from `self.env.company` (ANALYTICENFORCE-002, still open). Covered by tests in `tests/test_analytic_enforce.py` (two valid bills, valid + invalid bill, customer invoice + bill, single invalid bill, validation disabled).
- **Location:** models/account_move.py, action_post().
- **Trigger:** Enable validation and post two vendor bills together.
- **Actual behavior / impact:** After superclass posting the override reads self.move_type on the entire recordset instead of iterating moves. Scalar field access on multiple records raises Expected singleton, rolling back posting.
- **Evidence:** Actual AST method with a batch mock enforcing scalar singleton access raised ValueError: Expected singleton: account.move(1, 2).
- **Suggested fix:** Iterate moves and validate each applicable invoice separately.
- **Validation needed:** Batch vendor bills, mixed document types and singleton posting.

## ANALYTICENFORCE-002 — P1: Validation uses the current company instead of the bill company

- **Status:** Fixed in 19.0.0.0.5 — `action_post()` reads `analytic_distribution_validation_enabled` from `move.company_id` of each vendor bill/refund/receipt instead of `self.env.company`, so mixed-company batches apply each company's switch. Covered by tests in `tests/test_analytic_enforce.py` (`test_bill_company_enabled_current_company_disabled`, `test_bill_company_disabled_current_company_enabled`, `test_mixed_company_batch`).
- **Location:** models/account_move.py, action_post().
- **Trigger:** Post a bill belonging to company B while the environment current company is A and both are allowed.
- **Actual behavior / impact:** The switch is read from self.env.company. If A disables validation and B enables it, an invalid B bill bypasses enforcement; reversing the switches wrongly enforces A policy on B bills.
- **Evidence:** Actual extracted method with current-company switch False, bill-company switch True and an empty distribution returned success. Company-specific setting is related to company_id in the settings model.
- **Suggested fix:** Read the switch from each move.company_id, including in batch posting.
- **Validation needed:** Different switches in two allowed companies and mixed-company batches.

## Review limitations

All eligible Python/XML source was read. Actual methods were exercised with isolated mock objects; no Odoo database posting or integration tests executed.
