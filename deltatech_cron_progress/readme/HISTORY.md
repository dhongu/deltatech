## 20.0.1.0.0 (2026-10-30)

- Port of the 18.0 and 19.0 module: `ir.cron._cron_report_progress(done, remaining)`
  reports through `_commit_progress` (which commits), with the same signature as in 18.0.
  "Run manually" loops by itself since 19.0, so the `_trigger()` fallback is kept only for
  direct calls from code.
