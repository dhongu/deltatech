## 18.0.0.1.0 (2026-10-30)

- The batch cron jobs use the native cron progress through the new
  `deltatech_cron_progress` helper instead of calling `_trigger()` on themselves:
  merge duplicate contacts / companies, normalize company names, delete old mail
  messages and delete generated PDFs (invoices, sale orders, pickings). A batch that
  makes no progress (dry run, failed delete, all merges failed) reports nothing
  remaining, so the job stops instead of looping.
- Merge duplicate contacts / companies: each group is merged in its own savepoint, so a
  failed merge no longer cancels the whole batch.
- Fix: *Normalize company names* updated the same companies forever, because names
  already normalized (`S.R.L.`, `S.A.`, ...) still matched the selection and the batch
  always started at offset 0. Only names not yet normalized are selected now, the stored
  `complete_name` is recomputed, and the administrators are notified once, at the end.
- Fix: *Delete mail messages* never corrected the mimetype of `.xml` attachments
  (`name = '%.xml'` instead of `LIKE`), failed with an SQL error when `exclude_models`
  was not set, and deleted the messages of the excluded models whenever more than one
  pattern was given (`NOT LIKE ANY` instead of `NOT LIKE ALL`).

## 18.0.0.0.10 (2026-10-22)

- Listed on Odoo Apps as *Database Cleanup Actions* (was *Deltatech Actions*). The technical name `deltatech_actions` does not change.
