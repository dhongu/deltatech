## 19.0.1.0.5 (2026-10-19)

- Fixed the `invalid input syntax for type integer: "virtual_N"` error when saving a form
  (e.g. the stock return wizard) after a one2many line that was never saved got deleted
  twice, for instance with Enter pressed twice on its trash icon: the second delete no
  longer sends a `DELETE` command with the line's virtual id to the server.

## 19.0.1.0.4 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 19.0.1.0.3 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
