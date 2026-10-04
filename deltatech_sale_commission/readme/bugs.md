# Identified bugs

Reviewed: 2026-10-01
Target version: Odoo 20.0
Scope: Initial static review. Full database integration tests have not been run.

## [P2] Inverted unit conversion in the sales margin report

**Status:** Fixed in 20.0.1.5.3 (port of 19.0.1.6.1). The quantity is now
`l.quantity * u.factor / NULLIF(u2.factor, 0)`, the direction of `uom.uom._compute_quantity()`; a zero
product factor gives an empty quantity instead of a division error. Test:
`tests/test_margin_report_uom.py` (invoice and refund in dozens for a product in units, compared with the
ORM conversion).

**Location:** `report/sale_margin_report.py:153–154` (`_sub_select()`). Line numbers refer to the reviewed source and may change.

### Cause

The SQL computes l.quantity / u.factor * u2.factor. Odoo 20 converts invoice units to product units using l.quantity * u.factor / u2.factor.

### Impact

The reported product_uom_qty is incorrect when invoice and product units differ. The finding concerns reported quantities; it does not establish an error in the monetary commission calculation.

### Reproduction

Invoice 2 dozens for a product measured in individual units, with invoice unit factor 12 and product unit factor 1. The report computes 0.1667 individual units instead of 24. The refund branch has the same conversion error.

### Recommended correction

Use l.quantity * u.factor / u2.factor in both branches, preserving the existing invoice/refund sign handling.

### Validation

The field units and conversion semantics were checked against the local Odoo 20 core. The actual core UoM conversion method was executed in isolation: 2 units with factor 12 convert to 24 units with factor 1.

## [P1] Delivered cost is not normalized to the invoice unit

**Status:** Open — documented, not fixed.

**Location:** `models/account_invoice.py:120–123; report/sale_margin_report.py:165–169`. Line numbers refer to the reviewed source and may change.

### Cause

get_purchase_price() divides move value by stock.move.quantity, whose unit is the move unit. It returns that price directly without converting it to the invoice line unit. The report then multiplies this cost by invoice-line quantity.

### Impact

A delivery in dozens and an invoice in individual units can inflate the reported stock cost and distort margin and commission. Summing quantities from moves with different units is also invalid.

### Reproduction

Deliver one dozen with total cost 120, then invoice 12 individual units. get_purchase_price() returns 120 rather than a per-invoice-unit cost of 10; multiplying by invoice quantity produces stock cost 1440 instead of 120.

### Recommended correction

Normalize move quantities to a common product unit before averaging, then convert the resulting unit cost to invoice_line.product_uom_id. Apply consistent handling to the fallback product cost.

### Validation

The actual get_purchase_price() method was executed in isolation with move value -120 and move quantity 1; it returned 120. Core move quantity units and the report cost multiplication were checked.

## COMMISSION-003 — P1: Commission rates lack company access rules

- **Status:** Fixed in 19.0.1.6.2 / 20.0.1.5.5 — global multi-company restriction on `commission.users` (`[('company_id', 'in', company_ids)]`; in 20 the row `commission_users_comp_rule` of `security/ir.access.csv`, in 19 an `ir.rule` in `security/security.xml`), and `write()` re-checks the access after a `company_id` change. Covered by tests in `tests/test_company_rules.py`.
- **Location:** `models/commission_users.py`; `security/security.xml`; `security/ir.model.access.csv`.
- **Trigger:** A Commission Manager allowed in company A reads or modifies a commission.users record belonging to company B.
- **Actual behavior:** The model has company_id and manager full CRUD ACLs, but no company record rule. The only company rule declared in the module applies to sale.margin.report. The journal/company consistency constraint permits a valid B journal/B company pair and does not check the requesting user's allowed companies.
- **Impact:** Other companies' commission rates and manager/director assignments can be read or changed, affecting financial commission reporting.
- **Evidence:** Complete rate model, ACLs and manifest-loaded security inspected; no database impersonation test executed.
- **Suggested fix:** Add a global company rule consistent with the report rule and validate cross-company configuration access.
- **Validation needed:** As an A-only manager, deny read/write/create/delete on B rates while retaining access to A.
