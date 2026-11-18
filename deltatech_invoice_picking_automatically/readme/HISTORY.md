## 19.0.1.0.0 (2026-11-18)

- Each transfer gets its own document, with its own quantities: a delivery gets a customer
  invoice, a customer return a credit note, a receipt a draft vendor bill and a return to vendor a
  draft refund. Backorders are invoiced separately. Depends on `deltatech_invoice_picking`
  (dhongu/deltatech#4033).
- Only transfers with a sale or purchase order are queued. A queued transfer without an order fails
  with a reason instead of staying in the queue (dhongu/deltatech#3583).
- New **Invoice Moment** on the operation type: *Scheduled* (default, as before) or *On validation*.
  The invoicing runs with system rights, so warehouse users need no invoicing rights. A failure keeps
  the reason on the transfer, shown on the form, with a **Retry Invoicing** button, an optional list
  column and the **Automatic Invoicing Failed** / **To Invoice Automatically** filters
  (dhongu/deltatech#4035).

## 19.0.0.0.7 (2026-10-22)

- Listed on Odoo Apps as *Auto-Invoice from Delivery* (was *Invoice Pickings Automatically*). The technical name `deltatech_invoice_picking_automatically` does not change.

## 19.0.0.0.6 (2026-10-09)

- Each automatic invoicing in the cron now runs in its own savepoint. An error
  (posting validation or database error) rolls back only that picking's work, so
  no orphan draft invoice is left behind, the picking is marked as failed and
  logged, and the other pickings of the run are still invoiced.

## 19.0.0.0.5 (2026-09-29)

- Own module icon, instead of the generic gears it had.
