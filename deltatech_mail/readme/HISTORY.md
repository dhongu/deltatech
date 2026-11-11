## 19.0.1.0.8 (2026-11-11)

- Apps Store page: a fuller description (what the module does, the problem it solves, its main functions, dependencies and limits). No change in behavior.

## 19.0.1.0.7 (2026-11-07)

- Security: only administrators (Settings) can create or change email and body
  substitutions. Before, any internal user could add a "Receiver" rule that
  redirected every outgoing email of the database, or a body rule that changed
  the messages of all users. Internal users keep read access.
  (#3540)
- The body substitutions are read with sudo when posting, so authors without
  access to the rules (portal) still get them applied.

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
