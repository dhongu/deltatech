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
