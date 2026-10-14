## 20.0.0.0.7 (2026-10-14)

- Fix: the partner search on the number of agreements ("With agreement" filter) ignored the operator and the value and always returned the partners with agreements, even for `= 0`; it now honours the operator and counts the agreements with a grouped query instead of reading all of them.
- Fix: the number of agreements on the partner was computed with superuser rights; the count and the search now follow the same access rights and record rules (a user without access sees 0).
- Multi-company: global access restriction (`ir.access`) on the agreements (the agreements of the allowed companies only) and company consistency check of the partner.
- The User/Manager groups are shown under their own privilege ("Agreements", category Services) on the user form; a migration script links the existing groups.
- Agreement form: the status bar shows the real states (Draft, In Progress, Terminated) instead of a non-existent "quote" state.
- Agreement types: own list and form views (configuration menu).

## 19.0.0.0.6 (2026-10-11)

- Docs: emoji symbols added to the bold headings of the module description, for a uniform look on the Odoo Apps page. No code change.

## 19.0.0.0.5 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.0.0.4 (2026-09-30)

- New module icon in the flat style of the other modules; it replaces the old one.
