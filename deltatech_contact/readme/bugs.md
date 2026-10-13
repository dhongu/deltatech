# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## CONTACT-001 — P2: Phone-enriched contact names access the removed mobile field

- **Status:** Fixed in 19.0.1.4.10 — `_compute_display_name()` uses only `phone` (the field `mobile` no longer exists on res.partner in Odoo 19); a contact without a phone keeps its plain name. The commented-out legacy `_get_name` block was cleaned the same way. Covered by `tests/test_display_name.py` (with phone, without phone, without context).
- **Location:** `models/res_partner.py`, `_compute_display_name()`, lines 118–119.
- **Trigger:** Read a contact display name with `show_phone = True` when the contact has no phone number.
- **Actual behavior:** The fallback reads `partner.mobile`, which is absent from the Odoo 19 res.partner model.
- **Example:** An isolated execution with a contact lacking a phone raised an attribute error for mobile.
- **Impact:** Relational fields using the documented phone display context can fail to render.
- **Evidence:** Executed the existing override with a compatible minimal superclass and verified the local partner field declarations.
- **Suggested fix:** Use supported Odoo 19 contact phone fields and handle an empty phone without accessing removed fields.
- **Validation needed:** Display names with show_phone enabled for contacts with and without a phone, and the baseline without that context.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. CONTACT-001 was reproduced and fixed with database-backed tests (`tests/test_display_name.py`).

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **CONTACT-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.

## CONTACT-002 — P2: Nondigit CNP input raises an unhandled conversion error

- **Status:** Open.
- **Location:** models/res_partner.py, check_single_cnp(), _get_cnp_checksum() and create().
- **Trigger:** Enter/import a 13-character CNP containing a letter or separator, for example A234567890123.
- **Actual behavior:** The validator checks length but not numeric characters before calling int() for each digit and the checksum. ValueError escapes instead of returning False. create() invokes this validator before superclass creation, so its intended invalid-CNP clearing behavior cannot handle this input; write constraint likewise fails with a conversion error instead of the module's CNP invalid validation.
- **Evidence:** Actual AST-extracted validator/checksum with A234567890123 raised ValueError: invalid literal for int() with base 10: A. No Odoo partner mutation executed.
- **Impact:** Malformed identity input interrupts partner creation/import with an implementation exception and inconsistent invalid-input behavior.
- **Suggested fix:** Validate the accepted digit alphabet before numeric conversion and consistently apply the intended reject/clear policy across create/write.
- **Validation needed:** Nondigit first/middle/check digit, whitespace, empty values, short/long input, wrong checksum and valid digits, create and write/import paths.
- **Limitations:** Full eligible source reviewed; isolated validator methods only. No database import/contact tests executed in this pass. Historical CONTACT-001 remains fixed in source; its test execution claims were not rerun here.
