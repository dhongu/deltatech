## 20.0.0.0.7 (2026-10-16)

Migration to 20.0:

- The invoice analysis (`account.invoice.report`) is built from `_select_list()` in 20; the
  category type and class columns are added there (the `_select` / `_from` hooks are gone).
- `security.xml` had a stray `noupdate="0">` text node after `<odoo>`; removed.
- Access rights are declared in `ir.access`.
- Test adapted: in 20 every regular group implies `base.group_user_regular`.

## 19.0.0.0.7 (2026-10-11)

- Docs: emoji symbols added to the bold headings of the module description, for a uniform look on the Odoo Apps page. No code change.

## 19.0.0.0.6 (2026-10-09)

- Fix CATEGORYGROUP-001: the "Manage category groups" group implied the IDs of the root and
  admin users as if they were groups (e.g. "Access Rights"); these users are now members of
  the group, and the upgrade removes the wrong implied groups.

## 19.0.0.0.5 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.0.0.4 (2026-09-29)

- Own module icon, instead of the generic gears it had.
