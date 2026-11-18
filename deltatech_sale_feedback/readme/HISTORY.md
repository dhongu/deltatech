## 19.0.1.0.9 (2026-11-18)

- Fixed: e-mails sent from any template (for example the AWB e-mail of a delivery) failed with
  *Base URL must be a string*, and the SMS sent right after failed on `/sms/status`. The module read
  `web.base.url` from the wrong context key and kept the empty result in the parameter cache, so
  every later call of the same user got no base URL.
- The company website now replaces `web.base.url` only for the feedback e-mail; the other e-mails
  keep the database base URL, as in standard Odoo.

## 19.0.1.0.8 (2026-11-03)

- Description rewritten after the code: the per-line rating links, the scheduled action and the
  manual *Request feedback* action; the *Email feedback after sale* setting is documented as not used.
- Added a Limitations section: on 19.0 the sending fails on Odoo APIs that no longer exist.
- Summary and Apps banner no longer promise automatic sending configured from the settings.

## 19.0.1.0.7 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.0.6 (2026-09-29)

- Own module icon, instead of the generic gears it had.
