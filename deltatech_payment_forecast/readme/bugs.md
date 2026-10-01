# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## FORECAST-001 — P2: Company-currency amounts use the invoice currency label

- **Status:** Fixed in 19.0.0.0.3. Forecast lines now store `invoice.company_currency_id`, the currency of the signed amounts. A post-migration script relabels existing rows. Test: `test_forecast_001_company_currency_label`.
- **Priority:** Re-evaluated from P1 to P2 (2026-10-01): the amounts were numerically correct in company currency; only the currency label was wrong.
- **Location:** `wizard/payment_forecast_wizard.py`, `get_forecast_lines()` (lines 70–86).
- **Trigger:** Generate a forecast for an invoice whose currency differs from the company currency.
- **Actual behavior:** `amount_total_signed` and `amount_residual_signed`, which Odoo expresses in company currency, are stored with `invoice.currency_id`. The forecasted payment amount uses the same incorrectly labeled residual.
- **Example:** For a EUR invoice with a signed total of 500 RON, the forecast stores an amount of 500 with EUR as its currency.
- **Expected behavior:** The currency label and amounts use the same currency.
- **Impact:** Invoice totals, outstanding balances, and forecasted payments are displayed with incorrect currencies.
- **Evidence:** The local `account.move` definitions use `company_currency_id` for both signed fields. An isolated execution of the existing wizard method reproduced the mismatched currency and amount.
- **Suggested fix:** Use `invoice.company_currency_id` for these signed amounts, or consistently compute signed amounts in invoice currency if that is the intended reporting basis.
- **Validation needed:** A database-backed test with a foreign-currency invoice and a non-unit exchange rate.

## FORECAST-002 — P2: Recalculation deletes forecasts outside the selected company

- **Status:** Fixed in 19.0.0.0.3. `payment.forecast` has a `company_id` field and a multi-company record rule (`company_ids`). Manual and scheduled recalculation delete only the rows of the wizard company (`DELETE ... WHERE days = %s AND company_id = %s`, built with `SQL()`). The scheduled action runs once for each company of the cron user. A post-migration script sets the company of existing rows from their invoice. Tests: `test_forecast_002_*`.
- **Priority:** Re-evaluated from P1 to P2 (2026-10-01): the model had no ownership, so it was a global snapshot that one user overwrote for everyone, not a loss of accounting data.
- **Location:** `wizard/payment_forecast_wizard.py`, `get_forecast_lines()` (line 54) and `get_forecast_cron()` (line 98).
- **Trigger:** Generate a Custom forecast while another company or user already has Custom forecast rows. The scheduled entry point uses an equivalent global deletion for its day bucket.
- **Actual behavior:** SQL deletes every forecast row with the same `days` value, without company or user scoping and without applying ORM record rules.
- **Expected behavior:** Recalculation replaces only the rows belonging to the intended forecast scope.
- **Impact:** One recalculation removes other companies' or users' forecast results.
- **Evidence:** Isolated execution captured `DELETE FROM payment_forecast WHERE days = %s` with `Custom` as its sole filter. The forecast model currently has no company or user ownership field to scope replacement.
- **Suggested fix:** Define forecast ownership and company scope explicitly, then limit replacement to that scope in both manual and scheduled generation.
- **Validation needed:** Generate forecasts for two companies, recalculate one, and verify that the other company's rows remain.

## FORECAST-003 — P2: The company selected in the wizard is ignored

- **Status:** Fixed in 19.0.0.0.3. The invoice search filters on the wizard `company_id`. The payment-history search filters on `move_id.company_id` of the invoice and resolves account codes in the invoice company (`with_company`). `account.average.payment.report` was not changed: the filter goes through its existing `move_id` field, so `deltatech_average_payment_period` needs no new field. Tests: `test_forecast_003_*`.
- **Location:** `wizard/payment_forecast_wizard.py`, `company_id` (line 15) and `get_forecast_lines()` (lines 55–61).
- **Trigger:** Enable multiple companies, select one company in the wizard, and generate a forecast.
- **Actual behavior:** The invoice search does not use the selected `company_id`. It can include invoices from all companies visible in the current environment. The average-payment search also uses `sudo()` without a company filter.
- **Expected behavior:** Both invoices and payment history are limited to the company selected in the wizard.
- **Impact:** The report can mix invoices and payment history across companies, producing an incorrect company-specific forecast.
- **Evidence:** Isolated execution with a selected company confirmed that the invoice search domain contains no company condition. Source inspection confirmed that the payment-history domain also lacks company filtering.
- **Suggested fix:** Apply the selected company consistently to invoice and payment-history searches, and store the company on forecast rows to support filtering and access rules.
- **Validation needed:** A multi-company test with unpaid invoices and distinct payment histories for the same commercial partner.

## Review limitations

The findings were first verified through source inspection and isolated execution with mocked ORM objects. On 2026-10-01 they were reproduced with database-backed tests (`tests/test_payment_forecast_bugs.py`), which failed before the fixes and pass after them.
