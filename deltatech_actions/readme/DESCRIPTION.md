Features:

- Search and delete duplicate xml anaf files (cron: Delete duplicate xml attachments)
- Search and delete old pdf attachments of the invoices (cron: Delete duplicate xml attachments)
- Search and delete old pdf attachments of sale orders (cron: Delete pdf sale order attachments)
- All cron jobs are disabled by default and run in "dry mode" (no changes in the database)
- Cancel sale order function (including picking, stock moves and account moves linked). No server action defined, must
  be defined manually
