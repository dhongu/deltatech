Technical module that adds a common helper for batch cron jobs:
`ir.cron._cron_report_progress(done, remaining)`.

The helper uses the native cron progress of Odoo 18 (`_notify_progress`): when a batch
reports `remaining > 0`, the scheduler runs the job again right away (up to 10 times per
acquisition, then on the next poll), so the cron no longer has to call `_trigger()` on
itself after every batch.

Rules applied by the helper:

- `done == 0` forces `remaining = 0`, so a batch that made no progress stops the loop
  (mandatory for 19.0, where `done == 0` with `remaining > 0` is retried immediately);
- outside the scheduler ("Run manually", the cron monitor webhook or a direct call from
  code), Odoo 18 runs the job only once, so the helper calls `_trigger()` on the cron to
  process the rest in the background.
