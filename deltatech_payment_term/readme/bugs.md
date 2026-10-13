# Known bugs

Review date: 2026-10-03. Target version: Odoo 19.

## PAYTERM-001 — P2: A single percentage installment crashes before creating the term

- **Status:** Open.
- **Location:** wizard/payment_term.py, _check_rate(), do_create_rate().
- **Trigger:** Set value percent and rate 1, with an advance such as 25 percent.
- **Actual behavior:** The constraint accepts rate 1, but rest is assigned only when rate > 1. The rate loop reads rest for its first iteration, raising UnboundLocalError.
- **Impact:** A supported wizard input cannot produce a payment schedule.
- **Evidence:** Executed the actual AST-extracted method with rate 1: UnboundLocalError before any create/write. Existing test uses rate 3 only.
- **Suggested fix:** Compute the remaining percentage for every accepted rate, or consistently restrict the accepted range.
- **Validation needed:** One and multiple rates, advance 0/25/100, percent and fixed modes.

## PAYTERM-002 — P2: The requested installment day is ignored in due-date computation

- **Status:** Open.
- **Location:** wizard/payment_term.py, do_create_rate(); native account.payment.term.line._get_due_date().
- **Trigger:** Choose day of month 15 and create installments for an invoice dated January 31, 2026.
- **Actual behavior:** Generated lines set days_next_month but always use delay_type days_after. Native due-date logic ignores days_next_month in that mode and adds 30*x days. The first installment lands on March 2 rather than following the selected day; changing the selected day to 25 has no effect.
- **Impact:** Invoices use a schedule that does not reflect the requested monthly due day.
- **Evidence:** Executed actual generation and native _get_due_date with the generated first installment. Day 15 and day 25 both produced 2026-03-02.
- **Suggested fix:** Define the intended month progression and use the native due-date mode that applies the selected monthly day; validate month ends and the advance separately.
- **Validation needed:** January/February transitions, leap years, days 1/15/28/31 and multiple installments.

## PAYTERM-003 — P2: Invoice and partner Rates buttons reference an undefined action

- **Status:** Open.
- **Location:** models/account_invoice.py and models/res_partner.py, view_rate(); views/account_invoice_view.xml and res_partner_view.xml.
- **Trigger:** Click Rates on an invoice or partner after a clean installation.
- **Actual behavior:** Both methods resolve deltatech_payment_term.action_account_moves_sale, but the module ships no record with that external identifier. Its manifest-loaded XML defines wizard actions only.
- **Impact:** Both buttons fail during action lookup instead of opening the installments.
- **Evidence:** Checked the complete manifest and loaded XML, all local XML definitions, and the two callers. The identifier survives only in callers and translation metadata, which does not create an action. No database lookup executed; an upgraded database may retain an obsolete action and hide the defect.
- **Suggested fix:** Define and load the required action or use an existing native action with the appropriate structured domain.
- **Validation needed:** Clean installation and upgrade; invoice and partner buttons; action model/views and installment domains.

## Review limitations

Full eligible module source read and native contracts/dependent forecast and rating callers inspected. Executable isolated checks: audit_coverage/reproductions/payment_terms_history.py. These checks do not establish database lifecycle or access enforcement. No production operations or fixes applied.
