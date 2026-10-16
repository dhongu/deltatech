## 20.0.1.1.1 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 20.0.1.1.0 (2026-10-14)

- "Green Invoice" works again, on the Odoo 20 sending flow: for a partner with the flag, sending an invoice no longer downloads the PDF by default (the *Download* sending method is replaced by e-mail). The PDF can still be downloaded by ticking it in the wizard. In 18.0 the flag unticked the download in the old wizard; the override was removed in 19.0 because that wizard field no longer exists.

## 20.0.1.0.24 (2026-10-02)

- Remove the `account.move.send` override: it targeted `_compute_checkbox_download`, which does not exist in Odoo 20 either (the Send & Print machinery has no such computed field), so the "Green Invoice" flag on partners never did anything. The flag stays on the partner as an informative field (existing data is kept) and its help text no longer promises to block printing.

## 19.0.1.0.23 (2026-10-01)

- Fix: `address_get()` no longer fails when called without address preferences (e.g. from event registrations).

## 19.0.1.0.22 (2026-09-29)

- Own module icon, instead of the generic gears it had.
