# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## COMMISSION-001 — P2: The margin report converts invoice quantities using the inverse ratio

- **Status:** Fixed in 19.0.1.6.1. The quantity is now `l.quantity * u.factor / NULLIF(u2.factor, 0)`,
  the same direction as `uom.uom._compute_quantity()` and `sale/report/sale_report.py`; a zero product
  factor gives an empty quantity instead of a division error. The view is created with `SQL()`.
  Test: `tests/test_margin_report_uom.py` (invoice and refund in dozens for a product in units,
  compared with the ORM conversion; failed before the fix with 1/6 instead of 24).
- **Location:** `report/sale_margin_report.py`, `_sub_select()`, lines 153–154 and 197–198.
- **Trigger:** Report an invoice line whose unit differs from the product template unit.
- **Actual behavior:** SQL calculates `l.quantity / u.factor * u2.factor`; `u` is the invoice line unit and `u2` is the product unit. This is the inverse of Odoo 19 quantity conversion.
- **Example:** One dozen invoiced for a product measured in pieces appears as 1 / 12 pieces rather than 12. Refund quantities retain the sign but the magnitude is equally wrong.
- **Impact:** Quantity aggregates in sales margin and commission reporting are incorrect.
- **Evidence:** Verified the join aliases and compared the SQL expression with local `uom.uom._compute_quantity()`.
- **Suggested fix:** Use source factor divided by target factor, and protect against invalid factors.
- **Validation needed:** Compare invoice and refund report quantities with ORM conversion for non-unit ratios.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above.
COMMISSION-001 was reproduced and fixed with a database-backed test on 2026-10-01.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **COMMISSION-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.

## COMMISSION-002 — P2: Delivery cost sums quantities in different units without conversion

- **Status:** Open. Identified on 2026-10-02.
- **Location:** `models/account_invoice.py:74–145, get_purchase_price()`.
- **Trigger:** An invoice line is linked to done deliveries of the same product in different move units, such as one dozen and twelve pieces.
- **Actual behavior / impact:** The non-kit branch sums move.value but divides it by the sum of raw move.quantity. Those quantities are expressed in each move product_uom and cannot be added directly. It also returns the result without conversion to the invoice line unit. Stored purchase prices, margin amounts and commission calculations are incorrect.
- **Evidence:** Executed the extracted current get_purchase_price() with values 120 + 120 and quantities 1 dozen + 12 pieces: it returned 240/13 = 18.461538 rather than 10 per piece or 120 per dozen. The margin report multiplies purchase_price by invoice line quantity, so the returned cost must match that unit.
- **Suggested fix:** Convert each done quantity to a common product unit before aggregation, then convert the unit cost to invoice_line.product_uom_id. Preserve the existing refund and kit policies.
- **Validation needed:** Database-test homogeneous and mixed delivery units against the same invoice, including invoices in pieces and dozens; assert equal total cost and margin.
- **Limitations:** Extracted-method checks use mocked records; database-backed Odoo integration tests were not run in this pass.

## COMMISSION-003 — P1: Commission rates lack company access rules

- **Status:** Fixed in 19.0.1.6.2 — `security/security.xml` adds the `commission_users_comp_rule` multi-company rule on `commission.users` (created on upgrade even though the file is `noupdate`), and `write()` re-checks the access after a `company_id` change. Covered by tests in `tests/test_company_rules.py`.
- **Location:** `models/commission_users.py`; `security/security.xml`; `security/ir.model.access.csv`.
- **Trigger:** A Commission Manager allowed in company A reads or modifies a commission.users record belonging to company B.
- **Actual behavior:** The model has company_id and manager full CRUD ACLs, but no company record rule. The only company rule declared in the module applies to sale.margin.report. The journal/company consistency constraint permits a valid B journal/B company pair and does not check the requesting user's allowed companies.
- **Impact:** Other companies' commission rates and manager/director assignments can be read or changed, affecting financial commission reporting.
- **Evidence:** Complete rate model, ACLs and manifest-loaded security inspected; no database impersonation test executed.
- **Suggested fix:** Add a global company rule consistent with the report rule and validate cross-company configuration access.
- **Validation needed:** As an A-only manager, deny read/write/create/delete on B rates while retaining access to A.
