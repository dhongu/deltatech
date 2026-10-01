# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## CONTACT-001 — P2: Phone-enriched contact names access the removed mobile field

- **Status:** Open.
- **Location:** `models/res_partner.py`, `_compute_display_name()`, lines 118–119.
- **Trigger:** Read a contact display name with `show_phone = True` when the contact has no phone number.
- **Actual behavior:** The fallback reads `partner.mobile`, which is absent from the Odoo 19 res.partner model.
- **Example:** An isolated execution with a contact lacking a phone raised an attribute error for mobile.
- **Impact:** Relational fields using the documented phone display context can fail to render.
- **Evidence:** Executed the existing override with a compatible minimal superclass and verified the local partner field declarations.
- **Suggested fix:** Use supported Odoo 19 contact phone fields and handle an empty phone without accessing removed fields.
- **Validation needed:** Display names with show_phone enabled for contacts with and without a phone, and the baseline without that context.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
