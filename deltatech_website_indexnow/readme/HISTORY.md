# History

## 20.0.1.0.0 (2026-11-14)

- Migration to Odoo 20.0: the key file `/<key>.txt` finds the website of the host from the
  context (`website_id`, else `host_id`), `get_current_website()` being gone.

## 19.0.1.0.0 (2026-11-02)

- First version: the IndexNow key file served at `/<key>.txt`, the published pages and the
  published records of the website apps changed in the last hour sent by a scheduled action, and
  a *Send all pages now* button in the website settings.
