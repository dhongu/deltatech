## 18.0.0.0.6 (2026-10-30)

- **Each picking is invoiced in its own savepoint.** An SQL error on one picking
  (constraint, serialization) no longer aborts the cursor for the rest of the batch.
  The failed picking is set to `failed`, with the error in its chatter.

## 18.0.0.0.5 (2026-10-22)

- Listed on Odoo Apps as *Auto-Invoice from Delivery* (was *Invoice Pickings Automatically*). The technical name `deltatech_invoice_picking_automatically` does not change.
