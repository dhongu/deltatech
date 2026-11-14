In a consumer module, `tests/test_screenshots.py` extends `ScreenshotCase`, seeds deterministic data
in `setUpClass` and lists the screenshots in `capture_screenshots([...])`. The import is defensive,
so the module's tests still load when this tooling module is not on disk:

```python
try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None
```

Run:

```
./odoo/odoo-bin -c odoo.conf -d <db> -u <module> \
    --test-tags=fise_screenshots --stop-after-init --http-port=<free> --gevent-port=<free>
```

**Screenshots are generated only on request.** Unlike a normal test, they *write* to the working
tree (they rewrite the `.png` files of the module), so a test run that did not ask for them skips
them. They count as requested when:

- `--test-tags` contains the class's own tag (`fise_screenshots`, or any tag ending in
  `_screenshots`), as in the command above;
- `--test-tags` names the class, e.g. `--test-tags=/<module>:TestXScreenshots`;
- `FISE_SCREENSHOTS=1` is set in the environment.

`SKIP_FISE_SCREENSHOTS=1` is a veto over any request.

**Two languages.** The consultant sheet (`readme/FISA_CONSULTANT.md`) uses Romanian screenshots;
`readme/USAGE.md`, published on the Apps Store, uses English ones. Build the shot list once and
capture it per language:

```python
def _shots(self):
    return [{"url": ..., "name": "01_list.png", "highlight": "button[name='action_post']"}]

def test_capture_fise(self):  # ro_RO -> static/description/ (or readme/screenshots/)
    self.capture_screenshots(self._shots())

def test_capture_usage(self):  # en_US -> static/description/en/
    self.capture_screenshots(self._shots(), lang="en_US")
```

Prefer selectors by `name`; when a selector needs UI text, give it per language:
`{"ro_RO": "button:has-text('Confirmă')", "en_US": "button:has-text('Confirm')"}`.
To capture a single language, name the method:
`--test-tags=/<module>:TestXScreenshots.test_capture_usage`.

Framing: `capture_screenshots(..., viewport=(1920, 950))` by default, wide enough for
`account.report` tables with many columns; `force_light_theme()` is called by
`prepare_ro_company` / `prepare_demo_company`; `_autotrim` trims the margins. Useful per-shot
options: `full`, `wait`, `click_btn`, `click_tab`, `unfold_report`, `eval` (custom JS), `settle`
(pause in ms).

**Animated demo (GIF).** `capture_gif(steps, name="demo.gif")` records a flow as an animated GIF
for the Apps Store page: a simulated cursor glides to each target and shows a ring on click, text
is typed letter by letter and captions run at the bottom like film subtitles. The GIF opens with a slide
built from `static/description/banner.json` and the module icon, fades into the flow and returns
to the slide at the end. Each step is a dict; its keys run in this order:

```python
def test_capture_gif(self):
    self.capture_gif([
        {"goto": f"action={action.id}&model=res.partner&view_type=form"},
        {"caption": "A new partner starts with the name"},  # stays until the next one
        {"type": "Ferma Verde SRL", "into": "name"},     # a field name or any selector
        {"caption": "Once saved, the partner is ready"},
        {"click": ".o_form_button_save", "wait_after": ".o_form_saved", "hold": 2000},
    ], name="demo.gif")
```

Other keys: `path`, `wait`, `eval`, `move` (cursor only), `press` (`Enter`, `Tab`...), `clear`,
`hide_cursor`, `hold` (ms). Values may depend on the language, as in `capture_screenshots`;
`intro={"title": ..., "summary": ..., "features": [...]}` overrides the slide (e.g. Romanian texts
when `banner.json` is in English) and `intro=False` drops it. The GIF is 1120×700 by default
(`viewport`); `scale=0.75` makes a smaller file. Time in the GIF is virtual, so the pace does not
depend on how fast the server answers, and identical frames are merged. When a step fails, the
error names the step and saves the screen to a temporary `.error.png`.

Keep `static/description/en/demo.gif` (and `demo.gif` for the Romanian page): `tb-gen-index`
shows it automatically right under the hero of the Apps Store page, so do not reference it from
`readme/*.md` as well, or it appears twice.
