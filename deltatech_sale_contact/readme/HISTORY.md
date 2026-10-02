## 20.0.1.0.24 (2026-10-02)

- Remove the `account.move.send` override: it targeted `_compute_checkbox_download`, which does not exist in Odoo 20 either (the Send & Print machinery has no such computed field), so the "Green Invoice" flag on partners never did anything. The flag stays on the partner as an informative field (existing data is kept) and its help text no longer promises to block printing.

## 19.0.1.0.23 (2026-10-01)

- Fix: `address_get()` no longer fails when called without address preferences (e.g. from event registrations).

## 19.0.1.0.22 (2026-09-29)

- Own module icon, instead of the generic gears it had.
