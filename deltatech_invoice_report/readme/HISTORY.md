## 19.0.1.0.8

- [MIG] migrated to Odoo 19.0
- [REF] use `odoo.tools.SQL` builder in `_compute_invoice_history_sql` (mandatory in 19.0)
- [REF] port `_compute_invoice_history` from deprecated `read_group` to `_read_group` (tuple-based API, returns `date` for `:year` groupby)

## 18.0.1.0.8

- [FIX] add `refresh_invoice_history` on `product.product` (delegates to template); the button is inherited into `product.product_normal_form_view` and validation failed when only the template defined the method
