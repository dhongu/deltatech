## 20.0.1.4.13 (2026-11-03)

- Description rewritten from the code: an invalid CNP is cleared on every new
  contact, the form included, not only at bulk import; documented the silent
  correction of the check digit and the other CNP limitations, the contact name
  without the company and the hidden Contacts tab on company contacts.
- The Personal Data tab follows the Odoo 20 company definition (VAT number);
  the Persons and Companies filters are added by the module.

## 20.0.1.4.12 (2026-10-11)

- Docs: emoji symbols added to the bold headings of the module description, for a uniform look on the Odoo Apps page. No code change.

## 20.0.1.4.11 (2026-10-09)

- Apps Store banner (banner.json).

## 20.0.1.4.10 (2026-10-01)

- Tests for the contact display name with `show_phone`, for contacts with and without a phone (forward-port of the 19.0 CONTACT-001 fix; the 20.0 code already reads only `phone`).

## 20.0.1.4.9 (2026-09-29)

- Own module icon, instead of the generic gears it had.
