## 20.0.1.1.0 (2026-11-09)

- Data-only module: the empty `__init__.py` was removed, so the module has no Python code. It
  can be installed on Odoo Online (Custom plan) as a zip from Apps > Import Module, as well as on
  Odoo.sh and on-premise.
- Odoo Apps does not mark data-only modules as available on Odoo Online, so the module name,
  the summary, the banner and the Apps Store page now say it: "Sale Order Search by Contact
  (importable, Odoo Online)".
- Fixed: expanding the arrow next to **Search E-mail for** or **Search Phone for** and picking a
  contact returned an empty list (the filter received the contact id instead of the typed text).
  Both criteria now search on a text field, so they have no arrow and always use the typed text.
- Removed the Python test (`tests/`): Odoo Apps treats any `.py` file as Python code and would
  not mark the module as available on Odoo Online.

## 20.0.1.0.6 (2026-11-03)

- Description rewritten from the code: removed the search by mobile number,
  which the module does not offer (contacts have no separate mobile field in
  Odoo 20); named the search options and menus as they appear in the interface.

## 20.0.1.0.5 (2026-10-22)

- Listed on Odoo Apps as *Sale Order Search by Contact* (was *Sale Order Search by Partner Fields*). The technical name `deltatech_saleorder_search` does not change.

## 20.0.1.0.4 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 19.0.1.0.3 (2026-09-29)

- Own module icon, instead of the generic gears it had.
