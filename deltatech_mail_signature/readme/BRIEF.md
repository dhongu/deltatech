# Brief: deltatech_mail_signature

## Request

User, 2026-11-23: uniform e-mail signatures for everyone in the company, generated from a company
template with fields (name, job title, phone, company, ...), as at the Agroamat customer. It must be
a separate, reusable module for all e-mail sent from Odoo (chatter, quotations, invoices), not a
feature of the mail client `deltatech_mail_client`.

## Purpose

Each user writes (or forgets to write) their own signature in the preferences, so signatures differ
in layout, logo and data. The module keeps one signature template per company, written once in the
Odoo editor with images and `{{ ... }}` fields, and generates the signature of every internal user
(`res.users.signature`) from it. Everything that already uses the user signature (chatter e-mails,
`deltatech_mail_client`) gets it without further work.

## Who operates

Administrators (`base.group_system`) edit templates and generate the signatures of all users. Every
internal user can regenerate their own signature. Internal users can read the template.

## Scope (fit)

- Suite and technical name: `deltatech` / `deltatech_mail_signature`.
- New module; no existing module covers it (wiki, READMEs and code searched: the only signature code
  is the plain `res.users.signature` field of Odoo and the use of it in `deltatech_mail_client`).
- `depends`: `mail` (`res.users`/`res.partner` e-mail model and the chatter that sends the signature),
  `html_editor` (the HTML editor with image upload for the template body).
- New model: `mail.signature.template` (name, company, active, auto refresh, body).
- Extended: `res.users` (`mail_signature_generated`, boolean; override of `write`; action
  `action_regenerate_signature`), `res.partner` (`write` hook that refreshes generated signatures).

## Flow

1. The administrator opens Settings > Users & Companies > Signature Templates, creates the template of
   the company, writes the body in the editor, inserts the logo and fields such as `{{name}}`.
2. Saves: unknown fields are refused with the list of valid ones; images are checked and shared.
3. Clicks "Generate users' signatures": each internal user of the company without a hand-written
   signature gets the generated one; a notification says how many were generated and skipped.
4. A user changes their phone: their generated signature is refreshed automatically.
5. A user who wrote their own signature opens their preferences and clicks "Regenerate my signature"
   to switch to the company one.

## Fields

`{{name}}`, `{{job_title}}` (job position of the contact), `{{email}}`, `{{phone}}`, `{{mobile}}`
(mobile phone of the employee, empty when the HR app is not installed), `{{company}}`,
`{{company_website}}`, `{{company_phone}}`, `{{company_email}}`, `{{company_address}}` (one line),
`{{company_vat}}`.

## Acceptance criteria

- **CA1:** a template with `{{name}}` and `{{company}}` generates, for a user, a signature with their
  name and their company name.
- **CA2:** a value with HTML (`<script>`, `<b>`) is shown as text, never as markup.
- **CA3:** a line whose fields are all empty (e.g. "Tel: {{phone}}" without a phone) disappears with
  its label; a line with at least one filled field stays.
- **CA4:** saving a template with `{{unknown}}` (or a malformed `{{`) fails with an error that lists the
  valid fields; no signature ever contains a literal `{{...}}`.
- **CA5:** a link `href="{{company_website}}"` becomes `https://...` when the website has no scheme; a
  value such as `javascript:...` never ends in an `href`.
- **CA6:** a second active template for the same company is refused; two companies each have their own.
- **CA7:** "Generate users' signatures" fills the signature of all internal users of the company, marks
  them as generated, and does not touch users of another company or portal users.
- **CA8:** "Regenerate my signature" replaces the signature of the current user and marks it generated,
  also when it was written by hand.
- **CA9:** a hand-written signature (not marked) is not overwritten by the mass generation nor by the
  automatic refresh; editing a generated signature by hand removes the mark.
- **CA10:** changing the name, job position or phone of a user with a generated signature refreshes it
  (when the template has "Refresh automatically" on).
- **CA11:** only administrators create, edit and delete templates and use the mass generation; a user
  cannot regenerate the signature of someone else.
- **CA12:** images of the template are shared (public attachments), so recipients of chatter e-mails see
  them; the template accepts at most 5 images of 300 KB, PNG/JPEG/GIF, the limits of
  `deltatech_mail_client`; images pasted as `data:` are refused.
- **CA13:** record rules use `company_ids`: a user of company A does not see the template of company B.

## Edge cases

Multi-company: the template used for a user is the one of the user's default company. No active
template: the user action fails with a clear message, the mass generation too. Pressing the button twice
changes nothing. Archived users are skipped. Empty body: the template is not generated (error).

## Decisions taken

| Decision | Choice | Reason |
|---|---|---|
| Group | `base.group_system` only | no new group to maintain; the template is a company-wide setting |
| One active template per company | constraint, not auto-archive | silent archive would surprise the administrator |
| Mass generation and manual signatures | skipped; counted in the notification | the requirement: hand-written signatures are never overwritten |
| What is "hand-written" | signature not marked, with content beyond the user's plain name | Odoo fills a new user's signature with their name; that is not a hand-written signature |
| Mobile | `employee.mobile_phone` when `hr` is installed | `res.partner` has no mobile field in Odoo 19; no dependency on `hr` |
| Job title | `res.partner.function` | the field every user has without the HR app |
| Line removal rule | smallest block element (p, div, li, h1-6, td, th, tr) whose placeholders are all empty | predictable; "one field per line" is the documented way |
| Images | uploaded with the editor, attached to the template and made public | a recipient outside Odoo (and the mail client) must read them without login; see findings |
| Refresh trigger | `res.partner.write` and `res.users.write` on name, e-mail, phone, function, mobile | one place covers the contact form and the preferences |
| `deltatech_mail_client` | not touched | it already uses `res.users.signature` when the mailbox has none |

## Findings on images (checked in the code of Odoo 19 and of the mail client)

- The HTML editor uploads an image as a private `ir.attachment` with an `access_token` and writes
  `/web/image/<id>?access_token=...` in the HTML. `html_sanitize` keeps that `src`.
- Chatter e-mails put `user.signature` in the notification and `_replace_local_links` makes the URL
  absolute: an image works for an external recipient only when it is public or has the token.
- `deltatech_mail_client` accepts in a signature only `/web/image/<id>` (the query string is dropped,
  the token is lost) or `https` images, at most 5 of 300 KB, and embeds the attachment by `cid:` reading
  it with the rights of the user. A private attachment of another record is not readable by every user.
- Hence: the template turns its images into public attachments of the template, so both ways work, and
  applies the 5 / 300 KB / PNG-JPEG-GIF limits of the client at save.

## Out of scope

HTML help text in the mailbox form of `deltatech_mail_client` (separate follow-up); signature per
user group or per department; several templates per company; automatic refresh when the employee
record (HR) changes; a dedicated access group; plain-text signatures.
