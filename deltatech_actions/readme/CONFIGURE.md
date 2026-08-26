All scheduled actions provided by this module are **disabled by default**, and by default run in
**dry mode** (`dry_run`), meaning they only log what would be deleted without making any changes.

Their parameters live in **Settings > General Settings > Database Cleanup** (a dedicated app
section, visible to system administrators) — nothing needs to be edited in the cron's code field
any more. Enabling a scheduled action itself is still done from
**Settings > Technical > Automation > Scheduled Actions**: review the parameters in the settings
screen first, switch its "Dry run" toggle off, then enable the corresponding scheduled action.

## Duplicate XML attachments

Cron: *Delete duplicate xml attachments*. Model: `account.move`. Removes duplicate XML (EDI/ANAF)
attachments on invoices.

Settings: invoices per run (default `10`), minimum duplicates before deletion starts (default
`10`), max deletions per invoice (default `50`), dry run (default on).

## Invoice PDF cleanup

Cron: *Delete pdf invoice attachments*. Model: `account.move`. Removes old auto-generated invoice
PDFs — **including the ones attached to the outgoing email message rather than to the invoice
itself**. Sending an invoice by email ("Send & Print") attaches its PDF to that message
(`ir_attachment.res_model='mail.message'`, with the message pointing at the invoice), not to the
invoice directly; on a real deployment this is where the overwhelming majority of invoice PDFs
actually lived (40k+ out of ~41k, against a handful directly on `account.move`), and every resend
leaves its own copy behind. Both are searched.

Settings: attachments per run (default `5000`), older than N days (default `90`), name pattern
(SQL `LIKE`, empty = all), dry run (default on).

## Sale order PDF cleanup

Cron: *Delete pdf sale order attachments*. Model: `sale.order`. Removes old auto-generated sale
order/quotation PDFs. Same settings shape as invoice PDF cleanup.

## AWB label cleanup

Cron: *Delete pdf pickings attachments*. Model: `stock.picking`. Clears the carrier AWB label PDF
(`label_attachment` field) on old, finished deliveries. On a real deployment this field alone
accounted for **~36 GB across ~150k pickings** — by far the largest single filestore consumer,
well ahead of anything invoice-related.

The label is regenerable on demand: `carrier_generate_label()` (in `deltatech_delivery`) re-fetches
it from the courier's API via `carrier_tracking_ref` whenever `label_attachment` is empty, and
`has_awb` stays `True` regardless, so nothing looks different in the picking's UI. The remaining
risk is entirely on the courier's side: for a shipment old enough, its API may no longer have the
label on file — **confirm the actual retention window with the courier(s) in use before enabling
the scheduled action.**

Settings: attachments per run (default `5000`), older than N days (default `180`), name pattern
(SQL `LIKE`, empty = all — real label filenames vary a lot by carrier, from the carrier's own
report name to a raw tracking number or the field's technical name, so a narrow pattern like
`"Label%"` silently matches only some of them), "only finished deliveries" and "only cancelled
deliveries" toggles (both on by default, so a delivery still in progress is never touched), dry
run (default on).

## Old messages cleanup

Cron: *Delete mail messages*. Model: `mail.message`. Removes old chatter messages and their
non-XML/ZIP/plain-text attachments (ANAF documents are always kept regardless of this setting).

Settings: messages per run (default `5000`), older than N days (default `90`), subject pattern
(SQL `LIKE`, empty = all), excluded models (comma-separated `LIKE` patterns, default
`business.%,project.%,helpdesk.%` — these keep their full message history), dry run (default on).

## Duplicate contacts / companies

Two crons: *Merge duplicate contacts by email* (individual contacts sharing the same e-mail) and
*Merge duplicate companies by VAT* (companies sharing the same VAT number), both via Odoo's
built-in `base.partner.merge.automatic.wizard`.

Settings: contact groups per run (default `10`), company groups per run (default `10`). These two
crons perform the merge directly — there is no dry-run mode.

## Create missing reordering rules (0/0)

Model: `product.product`. Creates stock reordering rules for storable products that have none.
Requires the `deltatech_auto_reorder_rule` module to be installed. No configurable parameters.

## Normalize company names

Model: `res.partner`. Standardizes legal-form suffixes in company names
(e.g. `srl` → `S.R.L.`, `sa` → `S.A.`, `pfa` → `P.F.A.`, `ii` → `I.I.`).
Processes up to 500 records per cron run. No configurable parameters.

## Force-cancel server action

The method `force_cancel_order_and_moves` on `sale.order` cancels a confirmed sale order together
with all its linked stock pickings, stock moves, stock move lines and account moves by writing their
state directly to `cancel`. **This bypasses normal workflow checks** and must be used with care.

To activate it, create a **Server Action** manually:

1. Go to **Settings > Technical > Actions > Server Actions**.
2. Create a new action on model `Sale Order`.
3. Set action type to *Execute Python Code* and call `record.force_cancel_order_and_moves()`.
4. Add the action to the sale order's *Action* menu if needed.
