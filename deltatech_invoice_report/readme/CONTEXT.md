## Business context

Purchasing and sales teams often need a quick answer to "how much of this
product did we buy or sell last year?" without running a dedicated report.
The standard Odoo product form does not show historical invoice quantities,
and the built-in Invoice Analysis report lacks regional or supplier dimensions
that are useful for distribution and manufacturing companies.

This module addresses both needs:

- It materialises yearly purchase/sales quantities directly on the product form
  so buyers and sales reps can see trends at a glance.
- It enriches the Invoice Analysis pivot with **Region** (partner state) and
  **Default Supplier** grouping dimensions, enabling regional sales analysis and
  supplier performance comparisons without custom SQL or BI tools.

The history table (`product.invoice.history`) is a transient materialised cache
— it is rebuilt in full by the daily cron, or on demand per product via the
Refresh button. The source of truth remains the posted `account.move` records.
