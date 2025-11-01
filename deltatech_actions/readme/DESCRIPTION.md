Features:

- Search and delete duplicate xml anaf files (cron: Delete duplicate xml attachments)
- Create missing stock reordering rules (cron: Create missing reordering rules (0/0))
- Search and delete old pdf attachments of sale orders (cron: Delete pdf sale order attachments)
- All cron jobs are disabled by default and run in "dry mode" (no changes in the database)
- Function to cancel all stock and account moves on a sale order - force_cancel_order_and_moves. Must be called by
  server action. Create server action manually, for security reason
