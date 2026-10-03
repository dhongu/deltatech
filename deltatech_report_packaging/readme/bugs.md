# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## PACKMAT-001 — P2: Packaging material totals ignore invoice unit conversion

- **Status:** Open. Identified on 2026-10-02.
- **Location:** `models/account_move.py:37–61, refresh_packaging_material()`.
- **Trigger:** Invoice a product in dozens when packaging quantities are configured per piece, or mix invoice units for the same product.
- **Actual behavior / impact:** The method groups raw line.quantity by product and multiplies it by the configured material quantity. It never converts product_uom_id to product.uom_id, so equivalent physical quantities report different packaging consumption.
- **Evidence:** Executed the extracted refresh method for 1 dozen with 0.1 material units configured per product piece: it emitted 0.1 instead of 1.2. Source aggregation does not read invoice line UoM.
- **Suggested fix:** Convert each invoice line quantity to the product base unit before grouping and multiplying by material quantities.
- **Validation needed:** Compare packaging totals for 12 pieces versus 1 dozen, mixed-unit lines, purchase invoices and refunds.
- **Limitations:** Source comparison and isolated executions of extracted current methods with mocked records; no database-backed integration tests were executed.

## PACKMAT-002 — P2: Generating a report restores manually removed invoice packaging

- **Status:** Open.
- **Location:** wizard/invoice_packaging_material.py, do_report(); models/account_move.py, refresh_packaging_material().
- **Trigger:** Delete all invoice packaging lines intentionally, which disables packaging_material_auto, then generate Packaging materials report for that invoice.
- **Actual behavior:** The report refreshes any invoice without packaging lines, ignoring packaging_material_auto. Refresh reconstructs materials from products and re-enables automatic updates. Thus a reporting operation overrides an explicitly manual empty result.
- **Evidence:** Executed the actual AST-extracted report method with an empty manual invoice and a refresh shim: one refresh occurs, automatic updates become True and regenerated quantity 3 is reported. Complete refresh source confirms it recreates lines and sets the flag back. No invoice/database mutation executed.
- **Impact:** A zero/manual packaging correction is lost merely by generating a report; later posting can recompute values the user deliberately removed.
- **Suggested fix:** Respect the manual flag when initializing missing report values and avoid mutating manually maintained invoices during reporting.
- **Validation needed:** Manually deleted last line, explicitly disabled empty invoice, nonempty manual quantities and automatic invoices; reporting must preserve manual values/flags.

## PACKMAT-003 — P1: Invoice packaging records expose amounts and permit cross-company edits

- **Status:** Fixed in 19.0.1.3.2 — new `security/security.xml` with a multi-company rule on `packaging.invoice.material` through `invoice_id.company_id`; `create()`/`write()`/`unlink()` of the lines call `account.move._packaging_material_check_invoice_access()` (write access on the invoice, also on the target invoice when `invoice_id` changes), independent of the `packaging_material_sync` context. Covered by tests in `tests/test_company_access.py`.
- **Location:** security/ir.model.access.csv; models/account_move.py, InvoicePackagingMaterial and manual-mark hooks.
- **Trigger:** An internal user directly searches/reads packaging.invoice.material from inaccessible invoices, or writes them with packaging_material_sync=True in caller context.
- **Actual behavior:** The child model grants base.group_user full CRUD without invoice/company rules. It has no company field or explicit parent-access validation. Normally its manual-mark hook attempts a parent write, but the caller-controlled packaging_material_sync context bypasses that hook; direct child changes then do not need invoice write access.
- **Evidence:** Complete ACL, model hooks, manifest and views read. No security rules are loaded. _packaging_material_mark_manual_on_invoice returns immediately when the sync context is present, and child create/write/unlink otherwise use standard unrestricted child ACLs. No live packaging/account records accessed or modified.
- **Impact:** Invoice-associated quantities and IDs can be enumerated outside permitted companies; unauthorized callers can alter/delete quantities or create child rows for other invoices and corrupt packaging reporting.
- **Suggested fix:** Apply invoice/company access rules and explicit parent authorization to child CRUD; do not use a client-supplied context flag as an authorization substitute.
- **Validation needed:** Internal non-accounting users, two companies, restricted invoice reads/writes, direct child create/write/unlink and spoofed sync context; computed maintenance must remain authorized.

## Full source review — 2026-10-02

All eligible Python/XML files, including migrations, were manually read. Earlier findings remain open in the inspected source. New reproductions use AST-extracted methods with mock search/invoice objects; no browser, PostgreSQL search, migration or Odoo integration tests executed.
