## 19.0.1.0.1 (2026-10-25)

- `capture_screenshots` lifts Odoo's virtual memory limit (`limit_memory_hard`, RLIMIT_AS) while
  Playwright runs: Chrome inherited it and died at launch on Linux ("Target page, context or
  browser has been closed", SIGTRAP), as in CI. Odoo's own test browser already does this.

## 19.0.1.0.0 (2026-10-25)

- Moved here from `l10n_ro_doc_screenshots` (Romania localization suite, 19.0.1.1.9), in a public
  repository, so every suite and its CI can fetch it without access to a private one. The code is
  the same; `l10n_ro_doc_screenshots` now re-exports `ScreenshotCase` from this module.
