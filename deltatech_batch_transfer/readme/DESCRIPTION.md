Extends Odoo's batch transfer (batch picking) functionality to give warehouse operators
better control over batches that contain partially-processed or empty transfers.
Prevents Odoo's default behaviour of validating zero-quantity pickings and adds a
"Prepare Batch" wizard for quickly grouping receipts or deliveries from sales/purchase
orders into a single batch.

**Key features:**

- **Empty-picking management on validate** — when the Validate button is pressed on a
  batch, pickings that have all done quantities equal to zero are handled according to
  the `deltatech_batch_keep_pickings` system parameter:
  - *(default, parameter absent)* empty pickings are automatically removed from the
    batch; only non-empty pickings are validated. Removed pickings can be manually
    added to another batch.
  - *(parameter present)* empty pickings are kept in the batch but skipped during
    validation, allowing them to be processed later (not recommended with the barcode
    interface).
- **Prepare Batch wizard** — creates a new batch from open sale or purchase order
  receipts/deliveries for a selected partner; optionally sets done quantities from a
  product list.
- **Add to Batch button** — shortcut button on the stock picking form to attach a
  single transfer to an existing batch.
- **Extra batch fields** — `Direction` (incoming/outgoing), `Reference`, and `Note`
  added to the batch transfer form for better identification and traceability.
- **Received lines tab** — dedicated notebook tab on incoming batches showing only
  move lines with quantity > 0 (bold) vs. zero-quantity lines (muted).
- **Deliveries batch report** — PDF report that prints all delivery documents in a
  batch in a single action.
