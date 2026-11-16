## 19.0.1.1.0 (2026-11-16)

- Data-only module, importable on Odoo Online (Custom plan) from **Apps > Import Module**: the
  `__init__.py` files and the `tests/` folder were removed, because Odoo Apps treats any `.py`
  file as Python code and does not list the module as available on Odoo Online.
- The Python runner of the JavaScript tests (`tests/test_js.py`) and the screenshot test of the
  consultant sheet (`tests/test_screenshots.py`) were removed; the Hoot tests stay in
  `static/tests/` and run with the web unit tests (`/web/tests?filter=@deltatech_markdown_field`).
- The asset paths are listed file by file: an imported module rejects glob wildcards in asset
  paths.

## 19.0.1.0.7 (2026-11-14)

- Apps Store banner: the "Odoo Online" badge shows that the module has no Python code and installs on
  Odoo Online.

## 19.0.1.0.6 (2026-11-08)

- Fix: strikethrough, tables and task lists are no longer lost when the editor is left. The HTML → Markdown step now writes them back as `~~text~~`, GFM tables (with column alignment) and `[x]` / `[ ]` items; a table Markdown cannot express (merged cells, lists or paragraphs in a cell) is kept as HTML instead of being flattened. Values already flattened by an earlier save cannot be recovered.

## 19.0.1.0.5 (2026-11-07)

- Fix: the HTML produced from the Markdown is sanitized (DOMPurify) before it is displayed, in edit and in read-only mode. Scripts, inline event handlers, `javascript:` links and embedded content (`<iframe>`, `<object>`, `<embed>`) are removed; Markdown formatting and harmless inline HTML stay as they were.

## 19.0.1.0.4 (2026-10-22)

- Listed on Odoo Apps as *Markdown Field Widget* (was *Markdown Field*). The technical name `deltatech_markdown_field` does not change.

## 19.0.1.0.3 (2026-10-12)

- Fix: on servers with Python < 3.11 (rjsmin 1.1.0) the minified asset bundle broke on a regular expression of the vendored marked library (`Invalid regular expression: /^*-+:*$/`), stopping the backend in non-debug mode and the JS unit tests. The expression is now wrapped in parentheses, so it survives minification.

## 19.0.1.0.2 (2026-10-11)

- Docs: emoji symbols added to the bold headings of the module description, for a uniform look on the Odoo Apps page. No code change.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
