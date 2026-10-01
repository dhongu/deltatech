## 19.0.1.0.6 (2026-10-01)

- Fix: email redirection and the company sender work again on Odoo 19. The
  overrides used hooks that Odoo 19 no longer calls (`_send_prepare_values` on
  `mail.mail`, `_get_default_from` on `mail.message`), so substitutions and the
  "Use Company Email" option had no effect.
  - "Receiver" substitutions replace the recipients of every outgoing email
    (`_prepare_outgoing_list`); the CC copies are dropped, so the original
    recipients are not reached.
  - "Sender" substitutions set the sender. Before, with a document model they
    were added as a recipient.
  - "Use Company Email" sets the company address as sender of posted messages
    (`mail.thread._message_compute_author`) and of queued emails (`send`). An
    explicit sender (incoming email, template) is kept on posted messages.
    The `mail.message` override was removed.

## 19.0.1.0.5 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.4 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.
