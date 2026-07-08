This module provides maintenance actions, most of which run as scheduled actions (cron jobs). They are installed **inactive** by default; activate the ones you need from **Settings > Technical > Automation > Scheduled Actions** and adjust their parameters directly in the cron's Python code field before enabling them:

- **Delete duplicate xml attachments** — removes duplicate EDI/UBL XML attachments on invoices (`limit`, `duplicates`, `max_attachments_to_delete`, `dry_run`).
- **Create missing reordering rules** — creates missing stock reordering rules for storable products in bulk (requires `deltatech_auto_reorder_rule`).
- **Delete pdf invoice attachments** / **Delete generated pdfs** on pickings — purges old generated PDF attachments (`limit`, `pattern`, `max_date_days`, `dry_run`).
- **Delete old messages** — deletes old `mail.message` records (and their attachments) matching a subject pattern, age, or excluded models (`limit`, `pattern`, `max_date_days`, `dry_run`, `exclude_models`).
- **Merge duplicate contacts** — merges `res.partner` records that share the same email (individuals without a VAT number only).

Additional actions available on demand (not scheduled by default):

- **Force cancel order and moves** — on a Sale Order, forces cancellation of the order together with its linked pickings, stock moves, move lines and account moves, bypassing the normal cancel constraints.

Always run new/adjusted crons with `dry_run=True` first to review what would be affected before enabling deletions in production.
