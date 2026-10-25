The module installs as usual. Generating the screenshots needs extra packages in the Odoo Python
environment:

```bash
pip install playwright websocket-client pillow
playwright install chrome
```

- `playwright` — drives a headless Chrome to navigate and take the screenshots.
- `websocket-client` — talks to the Chrome DevTools Protocol.
- `pillow` — trims the margins of the screenshots (`_autotrim`); optional, without it the
  screenshot is saved untrimmed.
- **System Chrome** — `playwright install chrome` downloads the Chrome managed by Playwright.

Without `playwright`, the screenshot tests (`--test-tags=fise_screenshots`) are skipped instead of
failing.
