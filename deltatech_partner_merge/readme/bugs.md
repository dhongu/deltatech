# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## MERGE-001 — P1: Bulk merge ignores partner company access boundaries

- **Status:** Fixed in 19.0.1.0.3 — groups are built on (VAT, company) in `models/sql_queries.py` (BUILD_FACE/BUILD_GROUP/BUILD_MAP), the analysis is limited to the caller's active companies (shared partners only for system administrators or users with every company), and `action_apply()` calls `_check_partner_access()` (partners outside the scope, absorbed/master of different companies, `check_access` write and unlink on the partners). Covered by tests in `tests/test_company_scope.py`.
- **Location:** models/sql_queries.py, BUILD_FACE/BUILD_MAP/REMAP_FK/DELETE_ABSORBED; models/partner_merge_batch.py, action_analyze()/action_apply().
- **Trigger:** A company-limited user granted the module's Prepare/Apply roles analyzes duplicate VAT numbers present in inaccessible companies, or company-specific partners share a VAT across companies.
- **Actual behavior:** BUILD_FACE reads all active company-type partners directly from res_partner without company filtering or caller record-rule checks. Grouping and master selection use VAT alone. Apply checks the module role, then raw SQL updates references and deletes/archives absorbed partners globally, without partner access or company compatibility validation.
- **Evidence:** All selection/remap SQL and role ACLs inspected. Module roles are assignable independently of system administration. Neither candidate selection nor mutation predicates include company_id; no partner check_access call occurs. No database merge executed.
- **Impact:** A restricted operator can mutate/delete partners and references outside their allowed companies. Partners intentionally maintained separately per company can be merged into a master from another company, leaving company-specific documents attached to an incompatible partner.
- **Suggested fix:** Define explicit company scope, apply caller partner access checks and reject incompatible cross-company merges before building a map; require an explicit global administrative workflow for authorized global merges.
- **Validation needed:** Operator restricted to one company; same VAT in separate companies; shared partners; document partner/company consistency after an isolated merge.

## MERGE-002 — P2: Verification of an older batch uses the newest shared snapshot

- **Status:** Open.
- **Location:** models/sql_queries.py, BUILD_SNAPSHOT/VERIFY_TOTALS; models/partner_merge_batch.py, action_verify().
- **Trigger:** Apply batch A, analyze batch B, then open A and click Verify.
- **Actual behavior:** Every analysis drops/recreates global pm_snapshot and pm_map. action_verify only tests whether pm_snapshot exists and verifies those global tables, with no batch identity or relationship to self.line_ids. A therefore reports B's master counts and balances rather than validating A.
- **Evidence:** Complete analysis and verification paths inspected. Snapshot/map schemas have no batch_id. The single-in-progress guard allows a new batch after A reaches done, while the UI continues exposing Verify on A. No live merge or PostgreSQL verification executed.
- **Impact:** Historical verification can show success for unrelated records or misleading mismatches; the report does not establish whether the selected applied batch preserved its data.
- **Suggested fix:** Persist snapshots/maps by batch identity or record the working-table owner and reject verification when the retained snapshot belongs to another batch. Retain historical evidence for applied batches.
- **Validation needed:** Apply A, analyze/apply B, verify both; each report must use its own snapshot or clearly report unavailable evidence.

## Review limitations

All eligible Python/XML module source manually reviewed, including unique-index deduplication, foreign-key/polymorphic remaps, selection guards, savepoint simulation, field filling, archive/delete and verification. Findings are source-confirmed; no business-data merge, SQL DDL or PostgreSQL simulation executed.
