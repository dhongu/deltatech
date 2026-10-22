## 19.0.1.0.4 (2026-10-22)

- Listed on Odoo Apps as *Markdown Field Widget* (was *Markdown Field*). The technical name `deltatech_markdown_field` does not change.

## 19.0.1.0.3 (2026-10-12)

- Fix: on servers with Python < 3.11 (rjsmin 1.1.0) the minified asset bundle broke on a regular expression of the vendored marked library (`Invalid regular expression: /^*-+:*$/`), stopping the backend in non-debug mode and the JS unit tests. The expression is now wrapped in parentheses, so it survives minification.

## 19.0.1.0.2 (2026-10-11)

- Docs: emoji symbols added to the bold headings of the module description, for a uniform look on the Odoo Apps page. No code change.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
