# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## COMMISSION-001 — P2: The margin report converts invoice quantities using the inverse ratio

- **Status:** Open.
- **Location:** `report/sale_margin_report.py`, `_sub_select()`, lines 153–154 and 197–198.
- **Trigger:** Report an invoice line whose unit differs from the product template unit.
- **Actual behavior:** SQL calculates `l.quantity / u.factor * u2.factor`; `u` is the invoice line unit and `u2` is the product unit. This is the inverse of Odoo 19 quantity conversion.
- **Example:** One dozen invoiced for a product measured in pieces appears as 1 / 12 pieces rather than 12. Refund quantities retain the sign but the magnitude is equally wrong.
- **Impact:** Quantity aggregates in sales margin and commission reporting are incorrect.
- **Evidence:** Verified the join aliases and compared the SQL expression with local `uom.uom._compute_quantity()`.
- **Suggested fix:** Use source factor divided by target factor, and protect against invalid factors.
- **Validation needed:** Compare invoice and refund report quantities with ORM conversion for non-unit ratios.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
