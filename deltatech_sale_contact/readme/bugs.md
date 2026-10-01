# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## SALECONTACT-001 — P2: address_get fails when called without preferences

- **Status:** Open.
- **Location:** `models/res_partner.py`, `address_get()`, lines 17–18.
- **Trigger:** Call `partner.address_get()` using its supported default argument, for example through an event registration flow.
- **Actual behavior:** The superclass handles `None`, but the override then evaluates `"delivery" in adr_pref` where `adr_pref` is still `None`.
- **Example:** An isolated execution of the actual override with a compatible superclass raised TypeError: argument of type NoneType is not iterable.
- **Impact:** Standard flows relying on the default contact-address lookup fail while the module is installed.
- **Evidence:** Compiled and executed the existing override with a minimal superclass; verified that core `res.partner.address_get()` accepts the omitted argument and that event registration uses that call.
- **Suggested fix:** Normalize the preferences before checking membership while preserving the standard default behavior.
- **Validation needed:** Calls with no argument, None, an empty list, and explicit delivery/invoice preferences.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
