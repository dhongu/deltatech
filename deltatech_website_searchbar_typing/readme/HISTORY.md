## 19.0.1.2.0 (2026-11-16)

- Data-only module, importable on Odoo Online (Custom plan) from **Apps > Import Module**: the
  `__init__.py` files and the `tests/` folder were removed, because Odoo Apps treats any `.py`
  file as Python code and does not list the module as available on Odoo Online.
- The Python runner of the JavaScript tests (`tests/test_js.py`) was removed; the Hoot tests stay in
  `static/tests/` and run with the web unit tests
  (`/web/tests?filter=@deltatech_website_searchbar_typing`).
- The asset paths are listed file by file: an imported module rejects glob wildcards in asset
  paths.

## 19.0.1.1.1 (2026-11-14)

- Apps Store banner: the "Odoo Online" badge shows that the module has no Python code and installs on
  Odoo Online.

## 19.0.1.1.0 (2026-10-17)

- Website Builder option on the search box: "Typing examples" turns the animation on or off,
  and the prefix and the examples are edited in the panel, without the HTML editor.

## 19.0.1.0.0 (2026-10-17)

- First version: the placeholder of a website search box types the example searches given
  in the form, and stops on focus or typing. It respects `prefers-reduced-motion`, waits while
  the tab is hidden or the box is out of view, and keeps a stable accessible name.
