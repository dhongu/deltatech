## 20.0.1.2.2 (2026-11-19)

- Button icons use Odoo 20 Material Symbols names instead of Font Awesome classes, which Odoo 20 no longer styles: the buttons showed fragments of the icon name instead of the icon.

## 20.0.1.2.1 (2026-11-16)

- Empty `__init__.py` restored: the OCA tools (manifestoo, oca-checks-odoo-module) do not
  recognize a module without it, so the CI of the suites that depend on this module failed.
  The module still has no Python code and still imports on Odoo Online.
- Explicit Odoo Online marker: `"online": true` in `static/description/banner.json`
  (the banner no longer infers it from the missing `.py` files).

# 20.0.1.2.0

- A request created with a status (*Done*) is not sent to the server: a service module records with it
  a charge the server reported otherwise (e.g. the ANAF authorization of `l10n_ro_anaf_token_online`),
  so it shows in **Credit Usage** (forward port of 19.0.1.2.0).

# 20.0.1.1.0

- **Credit Usage**: each request keeps the credits it used and the credits left after it, as the
  Terrabit server answers them; a list, a graph and a pivot by service and month, with a total.
- **Settings > Terrabit Credits**: the services with their credits left and the credit usage, for
  the administrator, without the developer mode.
- **Credit Usage** button on the service form.
- **Credits Left** shows 3 decimals (forward port of 19.0.1.0.1): an answer may cost 0.001
  credits (one AWB), which showed as 0.00.

# 20.0.1.0.1

- Apps Store banner: the "IAP" label shows that the module works with IAP credits.

# 20.0.1.0.0

- Migration to 20.0: access rights in `security/ir.access.csv`, `get_str` for the database
  UUID, `index` of a manual field is a selection (`btree`).

# 19.0.1.0.0

- First version: services and requests, activation by callback, credits (refresh, buy), retry of a
  request without answer.
- Consultant sheet (`readme/FISA_CONSULTANT.md`), `readme/USAGE.md` and screenshots (RO, EN).
