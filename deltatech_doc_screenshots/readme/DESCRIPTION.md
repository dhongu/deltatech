A **development tooling** module: it adds no business feature.

It provides the `ScreenshotCase` mixin (in `tests/screenshot_case.py`) that generates the
screenshots of the consultant sheets (`<module>/static/description/`) **automatically**, from data
seeded deterministically in the tests.

How it works: `HttpCase` (the Odoo server and the test transaction) plus **Playwright** (system
Chrome) to navigate and take screenshots with clean names, written straight into
`<module>/static/description/`. Login through the session cookie.

**✨ Main features:**

- `ScreenshotCase` — reusable `HttpCase` base class for any consumer module: the screenshots are
  described as a list of dicts and generated with one command.
- `prepare_ro_company` — seeds the company with Romanian data (country, RON, VAT, address), gives
  the admin accounting rights and switches on the Romanian language and the light theme.
- `prepare_demo_company` — the alternative for modules with pre-filled demo data (invoices, etc.).
- `account_move_shot` — screenshot of an `account.move` form with the *Journal Items* tab open.
- `force_light_theme` — forces the light theme on the admin, whatever the database preference.
- `_autotrim` — trims the uniform margins of the screenshot.
- `highlight` per shot — outlines CSS/Playwright selectors in Odoo orange with numbered badges
  ①②③, to point at the exact steps of the sheet.
- Graceful degradation: without `playwright`, the screenshot tests are skipped and the test suite
  still passes.

It replaces `l10n_ro_doc_screenshots` (Romania localization suite), which now only re-exports
`ScreenshotCase` from here, so existing tests keep working.
