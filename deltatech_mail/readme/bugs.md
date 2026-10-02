# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## MAIL-001 — P1: Email redirection rules are ignored

- **Status:** Fixed in 19.0.1.0.6. Recipient and sender handling moved to the
  Odoo 19 flow: "receiver" substitutions are applied in `_prepare_outgoing_list()`
  (every per-recipient email is redirected, CC copies dropped), the sender
  (company email, then a "sender" substitution) is set in `send()` before Odoo
  reads `email_from` and picks the mail server. The equally dead
  `mail.message._get_default_from()` override was replaced by
  `mail.thread._message_compute_author()`, so `mail.use_company_email` applies
  again to posted messages. Covered by `tests/test_mail_redirect.py`.
- **Location:** `models/mail_mail.py`, `_send_prepare_values()` (lines 14–15);
  `models/mail_message.py`, `_get_default_from()`.
- **Trigger:** Configure a recipient substitution and send an email through the standard Odoo mail queue.
- **Actual behavior:** The email is sent to the original recipients. The substitution logic does not run because Odoo 19 does not call `_send_prepare_values()`.
- **Expected behavior:** Configured substitutions are applied before sending the email.
- **Impact:** Emails intended to be redirected can reach their original recipients. The company sender override in the same method is also skipped.
- **Evidence:** The local Odoo 19 mail implementation uses `_prepare_outgoing_list()` in `odoo/addons/mail/models/mail_mail.py`. Neither a definition nor a call to `_send_prepare_values()` exists in the core mail addon. Calling the custom method directly would also fail at its `super()` call.
- **Suggested fix:** Port recipient and sender handling to the Odoo 19 outgoing-mail preparation flow, preserving recipient-specific delivery behavior.
- **Validation needed:** Integration tests that send queued emails with receiver substitutions and with the company sender option enabled. Existing module tests cover substitution records and message-body replacement, but not outgoing email redirection.

## Review limitations

The finding was confirmed on origin/19.0 on 2026-10-01 and fixed the same day;
the tests send queued emails through the mocked mail gateway.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **MAIL-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.
