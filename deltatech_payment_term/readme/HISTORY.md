## 19.0.2.0.6 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.2.0.5 (2026-10-02)

- Recreate the `action_account_moves_sale` action (missing since 16.0) on top of `account.move.line`: the "Rates" buttons on invoices and partners raised an error on click. The invoice button lists the payment term lines of that invoice (one per rate, with due date and residual); the partner button lists the open customer rates of posted invoices. The domains are built in Python instead of string concatenation. Tests cover both buttons.

## 19.0.2.0.4 (2026-10-02)

- Fix the rates wizard: the `Advance` field used a non-existent decimal precision (`Payment Term`, now `Payment Terms`); with a single rate in percent mode the wizard crashed (`rest` undefined); the constraints on rate and advance only checked the first record; `do_create_rate` now calls `ensure_one()`. Tests cover the wizard, defaults, constraints, the rates flags and the views.

## 19.0.2.0.3 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.2.0.2 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.
