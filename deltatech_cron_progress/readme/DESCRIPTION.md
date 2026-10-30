Technical module that adds a common helper for batch cron jobs:
`ir.cron._cron_report_progress(done, remaining)`.

The helper uses the native cron progress of Odoo 19 (`_commit_progress`): when a batch
reports `remaining > 0`, the scheduler runs the job again right away (at least 10 runs and
10 seconds per acquisition, then on the next poll), so the cron no longer has to call
`_trigger()` on itself after every batch. "Run manually" loops the same way.

Rules applied by the helper:

- `done == 0` forces `remaining = 0`, so a batch that made no progress stops the loop
  (in 19.0, `done == 0` with `remaining > 0` is otherwise retried right away);
- in a cron run the progress is **committed** (`_commit_progress`), so it survives a
  timeout of a later batch;
- outside a cron run (direct call from code) nothing is committed and the helper calls
  `_trigger()` on the cron it is called on, to process the rest in the background.

The same signature exists in the 18.0 version of the module, so the cron code that uses
it is the same on both versions.
