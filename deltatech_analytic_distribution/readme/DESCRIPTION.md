This module enforces strict analytic distribution rules on vendor bills, ensuring every
invoice line is fully allocated across the company's analytic dimensions before posting.

**Key features:**

- Blocks posting of vendor bills (invoices, refunds, receipts) when any line is missing
  an analytic distribution.
- Validates that the total analytic distribution percentage on each line sums to exactly
  100%.
- Enforces that each distribution entry covers exactly three analytic dimensions:
  Location, Department, and Line of Business.
- Company-specific setting — can be enabled per company via Accounting configuration.
