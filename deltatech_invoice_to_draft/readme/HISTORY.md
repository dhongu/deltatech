## 19.0.2.0.4 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 19.0.2.0.3 (2026-10-07)

- Fix (DRAFTACCESS-001): the *Can reset account move to draft* group was enforced only by hiding the
  *Reset to Draft* button. A remote call of `button_draft` (or `button_cancel` on a posted entry) and the
  *Cancel Entry* button now raise an access error for users outside the group. Server-side flows that
  reset an entry as part of another operation (payment back to draft, bank reconciliation, POS session
  closing) and the superuser are not affected.

## 19.0.2.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
