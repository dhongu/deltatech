- Features:
  - Configuration on picking type for automatic invoice creation.
  - Configuration on picking type for automatic invoice posting.
  - Cron job that automatically generates invoices for pickings marked for invoicing.
  - Efficiently handles multiple pickings for the same sale order by processing them together.
  - Error handling: if invoicing fails, the picking is marked as 'Failed' to avoid repeated failed attempts.

