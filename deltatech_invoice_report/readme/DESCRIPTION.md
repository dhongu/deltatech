Extends the standard Odoo invoice analysis report and the product form with
purchase/sales history data, making it easy to see how much of each product
was bought or sold in any given year without leaving the product record.

**Key features:**

- Adds **Region** (partner state) and **Default Supplier** fields to
  `account.invoice.report`, so invoice analysis can be grouped or filtered by
  customer region or primary supplier.
- Adds a **History** tab on the product template form showing yearly quantities
  invoiced (qty in from purchase invoices, qty out from sales invoices).
- A **Refresh** button on the History tab recomputes the history on demand for
  the current product using an optimised raw SQL query.
- A daily **cron job** (`Update Product Invoice History by Year`) keeps the
  history table up to date automatically across all products.
- A **View Invoices** button on both the product template and product variant
  form opens the Invoice Analysis report pre-filtered and grouped by year and
  move type for that product.
