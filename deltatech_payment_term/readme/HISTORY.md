## 20.0.2.0.6 (2026-10-11)

- Docs: emoji symbols added to the bold headings of the module description, for a uniform look on the Odoo Apps page. No code change.

## 20.0.2.0.5 (2026-10-09)

- Apps Store banner (banner.json).

## 20.0.2.0.4 (2026-10-02)

- Recreate the `action_account_moves_sale` action (missing since 16.0) on top of `account.move.line`: the "Rates" buttons on invoices and partners raised an error on click. The invoice button lists the payment term lines of that invoice (one per rate, with due date and residual); the partner button lists the open customer rates of posted invoices. The domains are built in Python instead of string concatenation. Tests cover both buttons.

## 19.0.2.0.3 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.2.0.2 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.
