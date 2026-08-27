## 19.0.0.7.0

- The invoice, sale order and AWB label cleanups can now also run from Odoo's daily
  auto-vacuum job, controlled by a new switch in Settings > General Settings >
  Database Cleanup ("Run cleanups from the auto-vacuum job"), off by default.
  This exists for restored copies: `base/data/neutralize.sql` switches *every*
  cron off except `base.autovacuum_job`, so a neutralized staging database cannot
  tidy itself up through the crons. Another module's `neutralize.sql` cannot switch
  a cron back on either -- `neutralize_database()` iterates the installed modules in
  the arbitrary order Postgres returns them, so `base`'s blanket disable may run
  last and undo it. Hanging the cleanup off the auto-vacuum job is the only
  order-independent way.
- Each hook returns `(done, remaining)`, the shape `_run_vacuum_cleaner` uses to
  requeue a method within the same run, so a large backlog is cleared in one pass
  instead of one batch per day -- inside the cron's own time budget. A dry run never
  reports work remaining: it selects the same rows every call, and would otherwise
  spin until the cron ran out of time, starving the other vacuum methods.

## 19.0.0.6.0

- Cron code no longer carries call arguments. The cleanup crons ship in a
  `noupdate="1"` data file, so the `code` field of an already-created cron is
  frozen the day the database is created -- every later change to those
  arguments was silently ignored. Measured on a production instance: the module
  reported 19.0.0.5.0 while its AWB label cron was still running
  `cron_clean_generated_pdfs(limit=50, pattern="Label%", max_date_days=90)`, a
  limit five times smaller than the daily inflow and a pattern matching less
  than 60% of the real label names, with not a single `deltatech_actions.*`
  system parameter in the database. Nothing failed and nothing was logged: the
  crons ran green every night and deleted almost nothing.
- Added a migration that rewrites the `code` of existing crons to the
  parameterless `*_from_settings()` entry points. To keep the switch from
  changing what a cron deletes, the arguments found in the old code are copied
  into the matching system parameters first: an argument written explicitly in
  the old call wins, one the old call never passed keeps the module default.
  Parameters already set from the Settings screen are never overwritten, and a
  cron edited by hand is left untouched with a warning in the log.
- Added tests asserting that no cron in the data file passes arguments and that
  every method it names exists, so the problem cannot come back unnoticed.
