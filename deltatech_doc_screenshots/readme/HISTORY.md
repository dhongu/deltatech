## 19.0.1.1.0 (2026-10-30)

- Screenshots in a second language: `capture_screenshots(shots, lang="en_US")` sets the user's
  language and the browser locale, renders `report_shot` reports in that language and writes the
  files to `static/description/en/` with the same names, for `readme/USAGE.md` on the Apps Store.
  Romanian (`ro_RO`, the default) still goes to the usual folder, for the consultant sheet.
- Any shot value can depend on the language, as `{"ro_RO": ..., "en_US": ...}` (e.g. a
  `:has-text(...)` selector); `click_tab` finds the tab by its English or Romanian label.
- `report_shot` follows the capture language by default (`lang="auto"`); an explicit code still
  pins it.

## 19.0.1.0.2 (2026-10-25)

- The screenshots for the Apps Store (`static/description/`) work again with Pillow 9.0.1, the
  version Odoo 19 pins on Python 3.10: they failed with "module 'PIL.Image' has no attribute
  'Quantize'", a name that exists only since Pillow 9.1.

## 19.0.1.0.1 (2026-10-25)

- `capture_screenshots` lifts Odoo's virtual memory limit (`limit_memory_hard`, RLIMIT_AS) while
  Playwright runs: Chrome inherited it and died at launch on Linux ("Target page, context or
  browser has been closed", SIGTRAP), as in CI. Odoo's own test browser already does this.

## 19.0.1.0.0 (2026-10-25)

- Moved here from `l10n_ro_doc_screenshots` (Romania localization suite, 19.0.1.1.9), in a public
  repository, so every suite and its CI can fetch it without access to a private one. The code is
  the same; `l10n_ro_doc_screenshots` now re-exports `ScreenshotCase` from this module.
