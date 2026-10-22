## 19.0.0.0.7 (2026-10-22)

- Listed on Odoo Apps as *Auto-Invoice from Delivery* (was *Invoice Pickings Automatically*). The technical name `deltatech_invoice_picking_automatically` does not change.

## 19.0.0.0.6 (2026-10-09)

- Each automatic invoicing in the cron now runs in its own savepoint. An error
  (posting validation or database error) rolls back only that picking's work, so
  no orphan draft invoice is left behind, the picking is marked as failed and
  logged, and the other pickings of the run are still invoiced.

## 19.0.0.0.5 (2026-09-29)

- Own module icon, instead of the generic gears it had.
