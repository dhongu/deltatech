## 18.0.1.0.1 (2026-10-30)

- Own module icon (clock with a refresh accent) instead of the generic gears, and an
  Odoo Apps banner (`static/description/main_screenshot.png`, from `banner.json`).

## 18.0.1.0.0 (2026-10-30)

- Initial version: `ir.cron._cron_report_progress(done, remaining)`, a common helper for
  batch cron jobs on top of the native cron progress (`_notify_progress`), with a
  `_trigger()` fallback for manual runs and direct calls.
