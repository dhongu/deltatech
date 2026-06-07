All scheduled actions provided by this module are **disabled by default** and run in **dry mode**
(`dry_run=True`), meaning they only log what would be deleted without making any changes.
Before activating a cron job, review its parameters and switch `dry_run` to `False`.

To configure the scheduled actions, navigate to **Settings > Technical > Automation > Scheduled Actions**.

## Delete duplicate xml attachments

Model: `account.move`. Removes duplicate XML (EDI/ANAF) attachments on invoices.

Parameters passed in the cron code field:

- `limit` — number of invoice groups to inspect per run (default: `10`)
- `duplicates` — minimum number of same-name attachments before deletion starts (default: `10`)
- `max_attachments_to_delete` — safety cap on attachments deleted per run (default: `50`)
- `dry_run` — set to `False` to enable actual deletion (default: `True`)

## Delete pdf invoice attachments

Model: `account.move`. Removes old generated PDF attachments from invoices.

Parameters:

- `limit` — maximum number of attachments to delete per run (default: `5000`)
- `pattern` — name prefix filter, e.g. `"INV/%"` (empty string matches all)
- `max_date_days` — delete attachments older than this many days (default: `90`)
- `dry_run` — set to `False` to enable actual deletion (default: `True`)

## Delete pdf sale order attachments

Model: `sale.order`. Removes old generated PDF attachments from sale orders.

Parameters: same as *Delete pdf invoice attachments* (pattern example: `"Pro forma/%"`).

## Delete pdf pickings attachments

Model: `stock.picking`. Removes old generated PDF (and octet-stream) attachments from stock pickings.

Parameters: same as *Delete pdf invoice attachments* (default pattern: `"Label%"`).

## Delete mail messages

Model: `mail.message`. Removes old chatter messages and their linked attachments, excluding
ANAF/XML/ZIP/plain-text attachments.

Parameters:

- `limit` — maximum messages to delete per run (default: `5000`)
- `pattern` — optional subject filter, e.g. `"Facturx%"` (default: `"%"` = all)
- `max_date_days` — delete messages older than this many days (default: `90`)
- `exclude_models` — list of model name patterns to skip, e.g. `["business.%", "project.%", "helpdesk.%"]`
- `dry_run` — set to `False` to enable actual deletion (default: `True`)

## Create missing reordering rules (0/0)

Model: `product.product`. Creates stock reordering rules for storable products that have none.
Requires the `deltatech_auto_reorder_rule` module to be installed. No extra parameters.

## Merge duplicate contacts by email

Model: `res.partner`. Merges individual contacts (non-company, no VAT) that share the same e-mail address,
using Odoo's built-in `base.partner.merge.automatic.wizard`. Parameter: `limit` (pairs merged per run, default: `10`).

## Merge duplicate companies by VAT

Model: `res.partner`. Merges company records that share the same VAT number.
Parameter: `limit` (pairs merged per run, default: `10`).

## Normalize company names

Model: `res.partner`. Standardizes legal-form suffixes in company names
(e.g. `srl` → `S.R.L.`, `sa` → `S.A.`, `pfa` → `P.F.A.`, `ii` → `I.I.`).
Processes up to 500 records per cron run. No extra parameters to configure.

## Force-cancel server action

The method `force_cancel_order_and_moves` on `sale.order` cancels a confirmed sale order together
with all its linked stock pickings, stock moves, stock move lines and account moves by writing their
state directly to `cancel`. **This bypasses normal workflow checks** and must be used with care.

To activate it, create a **Server Action** manually:

1. Go to **Settings > Technical > Actions > Server Actions**.
2. Create a new action on model `Sale Order`.
3. Set action type to *Execute Python Code* and call `record.force_cancel_order_and_moves()`.
4. Add the action to the sale order's *Action* menu if needed.
