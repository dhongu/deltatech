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
