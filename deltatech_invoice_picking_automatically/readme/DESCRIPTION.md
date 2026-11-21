Invoices the validated transfers automatically, each transfer on its own document and with the
quantities it moved:

- delivery → customer invoice, posted when **Post Invoice Automatically** is set;
- customer return → customer credit note;
- receipt → vendor bill, always left in draft (it is posted when the vendor's document arrives);
- return to vendor → vendor refund, in draft.

Features:

- Configuration on the operation type: **Create Invoice Automatically**, **Invoice Moment** and
  **Post Invoice Automatically**.
- **Invoice Moment**: *Scheduled* (the daily scheduled action invoices the queued transfers, the
  default) or *On validation* (the transfer is invoiced right after it is validated).
- Backorders and partial deliveries are invoiced separately, with the quantities of each transfer.
  A transfer that is already invoiced is not invoiced again.
- Only transfers that come from a sale or a purchase order are queued.
- The invoicing runs with system rights, so a warehouse user without invoicing rights can validate
  transfers of an operation type that invoices on validation.
- Error handling: each transfer is invoiced in its own savepoint. If the invoicing fails, the transfer
  stays done, is marked **Failed** and keeps the reason, shown on the transfer. The **Retry
  Invoicing** button invoices it again after the cause is fixed.
- The **Automatic Invoicing** status on the transfer form and as an optional column in the list, and
  the **Automatic Invoicing Failed** and **To Invoice Automatically** filters.
