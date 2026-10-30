## 18.0.0.0.6 (2026-10-30)

- The invoicing cron runs each delivery in its own savepoint: a failing delivery is marked *Failed*, with the error in its chatter, and the rest of the batch is still invoiced.

## 18.0.0.0.5 (2026-10-22)

- Listed on Odoo Apps as *Auto-Invoice from Delivery* (was *Invoice Pickings Automatically*). The technical name `deltatech_invoice_picking_automatically` does not change.
