# Identified bugs

Reviewed: 2026-10-01
Target version: Odoo 20.0
Scope: Initial static review. Full database integration tests have not been run.

## [P2] Inverted unit conversion in the sales margin report

**Status:** Open — documented, not fixed.

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
