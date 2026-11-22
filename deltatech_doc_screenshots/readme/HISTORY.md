## 20.0.1.3.0 (2026-11-22)

- Forward-port of 19.0.1.5.0. `capture_gif`: smaller demo GIFs by default. `scale` defaults to
  0.8 (the default 1120×700 viewport gives a 896×560 GIF) and the new `colors` parameter (default
  128) sets the size of the global palette, now passed to `GifRecorder.save`. On the
  `deltatech_chatter` GIF (85 frames) this goes from 1.2 MB to about 880 KB with readable text;
  existing tests need no change.
- Consultant sheet: GIF size and palette in step 3 and in the checks; step 4 (XLSX exports) gets
  its screenshot (`02_export_xlsx.png`, made by the module test); the demo GIFs are regenerated at
  896×560.

## 20.0.1.2.0 (2026-11-18)

- Forward-port of 19.0.1.2.0 – 19.0.1.4.0 (see below), adapted to Odoo 20:
  - `capture_gif(steps, name)`: animated demo GIF for the Apps Store (`tests/gif_recorder.py`), with a
    simulated cursor, letter-by-letter typing, film-style subtitles and an opening/closing slide built
    from `banner.json` and the module icon. The slide follows the Apps banner: the version comes
    from the manifest ("Odoo 20", no longer a hard-coded "Odoo 19") and the edition from
    `banner.json` `edition` or, when missing, from the dependencies (Enterprise when the module or
    one of its dependencies has the `OEEL-1` licence), no longer always "Community". The GIF is always written to `static/description/` (`en/` for English).
  - `capture_screenshots` and `capture_gif` share the browser start-up (`_browser_session`); the Odoo 20
    helpers (`click_notebook_tab`, `render_all` / `unfold_report`, `screenshots_dir(lang)`) are kept.
  - `xlsx_to_html` / `xlsx_shot`: right-aligned numbers with the cell number format and `lang` separators.
  - Demo GIF of the tool itself (`test_capture_gif`), the GIF step in the consultant sheet and in USAGE.

## 19.0.1.4.0 (2026-11-14)

- `capture_gif`: the captions are film-style subtitles (white text centred at the bottom on a
  translucent black band that follows the lines), without step numbers; the `num` key is gone.
- A target that would end up under the subtitle is scrolled to the middle of the screen, and the
  Odoo content gets room at its end, so the last fields of a form can rise above the subtitle.
- The GIF is always written to `static/description/` (`en/` for English), also for modules that
  still keep their PNG screenshots in `readme/screenshots/`.
- `demo.gif` is no longer referenced from `readme/USAGE.md`: `tb-gen-index` 1.14.0 shows it first
  in the Overview tab of the Apps Store page.
- Consultant sheet: the demo GIF step (`capture_gif`), where the GIF is written and the checks.

## 19.0.1.3.0 (2026-11-14)

- New `capture_gif(steps, name)`: records a flow as an animated GIF for the Apps Store, with a
  simulated cursor (glide and click ring), letter-by-letter typing and numbered captions, opening
  and closing on a slide built from `banner.json` and the module icon. Global 256-colour palette
  (octree, so links and buttons keep their colour) and merged identical frames keep the file small.
- `capture_screenshots` and `capture_gif` share the browser start-up (`_browser_session`).

## 19.0.1.2.0 (2026-11-03)

- `xlsx_to_html` / `xlsx_shot`: numbers are right-aligned and shown with the cell number format
  (e.g. `#,##0.00` → two decimals, thousands separator); the new `lang` argument picks the
  separators (`ro_RO`: `1.234,56`).

## 20.0.1.1.0 (2026-11-02)

- Migration to 20.0. The mixin keeps the Odoo 20 fixes already made in
  `l10n_ro_doc_screenshots` 20.0.1.1.10: `click_tab` looks only among the notebook tabs (in 20.0
  they are `button.nav-link`, and a form button with the same text no longer catches the click),
  folded report lines are found by `[data-id="btn_foldable"]`, `render_all` / `unfold_report`
  render the whole report despite the virtual grid of `account_reports`, and the company masking
  clears `additional_identifiers` (formerly `company_registry`) and `account_number` (formerly
  `acc_number`).
- The tests of these page helpers (`test_screenshot_case.py`) come along with them.

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
