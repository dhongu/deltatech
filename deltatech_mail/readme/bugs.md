# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## MAIL-001 — P1: Email redirection rules are ignored

- **Status:** Open.
- **Location:** `models/mail_mail.py`, `_send_prepare_values()` (lines 14–15).
- **Trigger:** Configure a recipient substitution and send an email through the standard Odoo mail queue.
- **Actual behavior:** The email is sent to the original recipients. The substitution logic does not run because Odoo 19 does not call `_send_prepare_values()`.
- **Expected behavior:** Configured substitutions are applied before sending the email.
- **Impact:** Emails intended to be redirected can reach their original recipients. The company sender override in the same method is also skipped.
- **Evidence:** The local Odoo 19 mail implementation uses `_prepare_outgoing_list()` in `odoo/addons/mail/models/mail_mail.py`. Neither a definition nor a call to `_send_prepare_values()` exists in the core mail addon. Calling the custom method directly would also fail at its `super()` call.
- **Suggested fix:** Port recipient and sender handling to the Odoo 19 outgoing-mail preparation flow, preserving recipient-specific delivery behavior.
- **Validation needed:** Integration tests that send queued emails with receiver substitutions and with the company sender option enabled. Existing module tests cover substitution records and message-body replacement, but not outgoing email redirection.

## Review limitations

This finding was verified against the local Odoo 19 source. No database-backed mail delivery test was run, and no fix has been applied.
