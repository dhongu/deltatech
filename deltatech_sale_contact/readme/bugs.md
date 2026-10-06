# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## SALECONTACT-001 — P2: address_get fails when called without preferences

- **Status:** Fixed in 19.0.1.0.23 — `address_get()` normalizes the preferences with `set(adr_pref or [])` after calling super, as the core does, so calls without argument, with `None` or with an empty list return the standard result; covered by `test_05_address_get_without_preferences`.
- **Location:** `models/res_partner.py`, `address_get()`, lines 17–18.
- **Trigger:** Call `partner.address_get()` using its supported default argument, for example through an event registration flow.
- **Actual behavior:** The superclass handles `None`, but the override then evaluates `"delivery" in adr_pref` where `adr_pref` is still `None`.
- **Example:** An isolated execution of the actual override with a compatible superclass raised TypeError: argument of type NoneType is not iterable.
- **Impact:** Standard flows relying on the default contact-address lookup fail while the module is installed.
- **Evidence:** Compiled and executed the existing override with a minimal superclass; verified that core `res.partner.address_get()` accepts the omitted argument and that event registration uses that call.
- **Suggested fix:** Normalize the preferences before checking membership while preserving the standard default behavior.
- **Validation needed:** Calls with no argument, None, an empty list, and explicit delivery/invoice preferences.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. SALECONTACT-001 was fixed on 2026-10-01 and verified with the module's database-backed tests (5 tests, 0 failures).

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **SALECONTACT-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.

## Integrated review — 2026-10-03

SALECONTACT-001 fix retained. Entire source, native address_get, sending wizard, field/view/domain contracts read. Historical database tests not rerun.

### SALECONTACT-002 — P2: green-invoice download suppression uses an inactive API

The addon defines _compute_checkbox_download on account.move.send, expecting checkbox_download, mode and move_ids. Native Odoo 19 uses account.move.send.wizard sending_methods/sending_method_checkboxes and move_id, with download through _action_download when manual is selected. Native account code does not call or define the old hook. Setting partner.print_green_invoice therefore does not suppress download through this implementation. Adapt to the current sending workflow and explicitly choose intended UI/default/download policy. If invoked explicitly, the old method's super call has no native implementation, but that is not claimed as a normal-flow crash.

Evidence: complete addon and native send model/wizard methods searched and read. Source proof of inactive behavior; no database/UI download test executed. Field help promises no printing, whereas implementation only attempted download suppression; printing policy needs clarification.

### Limits

View anchors and declared dependencies exist. Partner domains deliberately restrict selection and do not constitute ORM constraints. Default-contact uniqueness is only normalized on write, not create; data/configuration invariant needs validation before a separate finding. No fixes or source migrations made.
