# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## ACTIONS-001 — P1: Contact merge detaches contacts that it does not merge

- **Status:** Fixed in 19.0.0.9.5. `parent_id` is cleared only on the merged pair. Covered by `test_merge_contacts_keeps_parent_of_unmerged_contacts`.
- **Location:** models/res_partner.py, `_cron_merge_duplicate_contacts()`.
- **Trigger:** Three or more individual contacts share an email, have no VAT and belong to parent companies.
- **Actual behavior:** The method writes parent_id=False to every contact in the duplicate group, then sends only the first two IDs to the merge wizard. The remaining contacts retain no company parent even though they were not merged.
- **Evidence:** Executed the actual extracted method with three contacts: merge IDs were [1, 2], while contact 3's original parent 50 became False. The duplicate query does not restrict parent_id. No database merge executed.
- **Impact:** Automatic deduplication silently removes commercial-company relationships from untouched contacts. Subsequent cron runs may eventually merge them, but the current run can leave detached records until then.
- **Suggested fix:** Modify only records included in the merge and preserve parent associations unless an explicit merge policy requires changing them.
- **Validation needed:** A three-contact group and contacts sharing an email across parent companies; verify both merged and unmerged commercial relationships.

## ACTIONS-002 — P2: Empty message exclusions supply a Boolean to SQL ANY

- **Status:** Open.
- **Location:** models/mail_message.py, `cron_clean_old_messages_from_settings()` and `cron_clean_old_messages()`.
- **Trigger:** Run old-message cleanup with no excluded models configured, or call the method without exclude_models.
- **Actual behavior:** The settings wrapper converts an empty list to False. Both SQL branches unconditionally use model LIKE ANY(exclude_models), which requires an array; False is a PostgreSQL Boolean, not an empty array. The query cannot select the cleanup batch.
- **Evidence:** Inspected the parameter construction and both SQL branches: empty text maps to False, and no conditional removal/conversion of the ANY predicate exists. Tests inspected supply a nonempty list, so those cases do not exercise this failure. Database query was not executed in this audit.
- **Impact:** Cleanup fails when the exclusion list is intentionally empty, including direct calls using the method's default.
- **Suggested fix:** Pass an empty string array or omit the exclusion predicate when no exclusions exist; handle messages whose model is NULL deliberately.
- **Validation needed:** Empty, single and multiple exclusion patterns, with and without a subject pattern, in dry-run and actual cleanup modes.

## Review limitations

All eligible module source has been manually read. Isolated mocks are not Odoo database tests; cleanup, cancellation and migrations were not executed on a database.

## ACTIONS-003 — P1: XML cleanup expands candidates by name and protects only one invoice

- **Status:** Fixed in 19.0.0.9.5. SQL groups by `res_id, name`; the ORM domain keeps `res_model`, `res_id` and `mimetype`; the newest copy is kept; `_get_xml_attachments_in_use()` protects the EDI documents and every `ir.attachment` many2one of that invoice. Covered by `test_xml_cron_counts_duplicates_per_invoice` and `test_xml_cron_keeps_attachment_used_by_invoice`.
- **Location:** models/account_move.py, `cron_clean_xml_attachments()`.
- **Trigger:** Multiple invoices have XML attachments with a common name, or another document has an attachment with the same name.
- **Actual behavior:** SQL groups by name across account.move XML attachments, but the subsequent ORM search restricts only name and optional age. It omits res_model, res_id and mimetype. EDI protection uses the invoice obtained from attachments[0].res_id; all attachments linked to other invoices remain in the deletion candidates.
- **Evidence:** Inspected the SQL grouping, ORM domain and single-invoice edi_document_ids subtraction. Deletion applies sudo.unlink to the resulting wider set; no destructive reproduction performed.
- **Impact:** Same-name attachments on unrelated models or valid XMLs on other invoices can be selected for deletion. This is not a per-invoice duplicate check. Other installed unlink protections may block individual cases.
- **Suggested fix:** Identify duplicates per invoice and document content/type; retain the original model/type restrictions and protect each invoice's EDI links.
- **Validation needed:** Shared filenames across invoices/models, different content under one filename, and EDI links for every invoice; assert only genuine duplicates are removed.

## ACTIONS-004 — P1: Public attachment cleanup bypasses caller authorization

- **Status:** Fixed in 19.0.0.9.4 — `check_cleanup_access()` (`models/cleanup_summary.py`, `env.is_system()`) runs before any SQL/`sudo()` in `cron_clean_generated_pdfs()` (account.move, sale.order, stock.picking), `cron_clean_xml_attachments()`, `cron_clean_old_messages()` and in `_dt_actions_run_now()`; the `*_from_settings` entry points go through them. Crons (run as `base.user_root`) and autovacuum keep working. Covered by tests in `tests/test_cleanup_access.py` (non-administrator rejected with nothing deleted, administrator and cron user allowed).
- **Location:** account_move.py, sale_order.py and stock_picking.py `cron_clean_generated_pdfs()`; mail_message.py `cron_clean_old_messages()`.
- **Trigger:** An internal user invokes a public cleanup method through ORM/RPC with dry_run=False.
- **Actual behavior:** The methods do not check an administrator group or caller model/record access. Raw SQL selects candidates across companies, then attachment/message deletion is elevated with sudo. Public method names remain callable independently of their administrator settings buttons or cron configuration.
- **Evidence:** Full method bodies inspected: no caller authorization checks or company predicates precede SQL/sudo.unlink. Direct cleanup methods default to actual deletion; the settings dry-run default does not protect direct calls. No live RPC or deletion executed.
- **Impact:** A caller can trigger deletion of old documents outside their allowed companies and ordinary attachment unlink rights.
- **Suggested fix:** Require explicit cleanup-administrator authorization before SQL/elevation, or expose only private cron methods and guarded public settings entry points.
- **Validation needed:** Non-administrator RPC calls and a disabled-company document must be rejected without selecting/deleting records; authorized admin cleanup must still work.

## ACTIONS-005 — P2: Run-now notification reports successful deletion after unlink errors

- **Status:** Open; source verified 2026-10-02.
- **Location:** models/res_config_settings.py, `_dt_actions_run_now()` and `_dt_actions_run_message()`; attachment/message cleanup methods.
- **Trigger:** Run actual cleanup and have attachment/message unlink raise an exception, for example from another installed module's deletion protection.
- **Actual behavior:** The cleanup catches/logs the exception but returns counts based on selected records. The settings button interprets dry_run=False as success and displays Cleanup done with a message saying those records were deleted.
- **Evidence:** All three PDF cleanup methods return their selected rows after the exception handler; rows_summary counts those rows. XML/message cleanup similarly returns candidate counts. The notification reads only dry_run/count/size, without an error result.
- **Impact:** Administrators receive a false success report when deletion failed or completed only partly; an autovacuum run can also report progress and retry based on the candidate count. SQL-level exceptions may separately abort the transaction.
- **Suggested fix:** Return an explicit failure/partial-success result and actual deleted counts, propagate unexpected errors, and show an accurate notification.
- **Validation needed:** Mocked unlink rejection plus database tests for protected attachments and partial cleanup; verify counts, notification and transaction outcome. No database tests executed.

## ACTIONS-006 — P2: Company-name normalization is public and rewrites partners without authorization

- **Status:** Open. Found on 2026-10-03 while fixing ACTIONS-004.
- **Location:** models/res_partner.py, `batch_normalize_company_names()` and `cron_normalize_company_names()`.
- **Trigger:** An internal user calls `res.partner.batch_normalize_company_names` (or `cron_normalize_company_names`) through ORM/RPC.
- **Actual behavior:** Both methods are public and perform no caller check: the batch method runs a raw SQL `UPDATE res_partner SET name = ...` on every company partner whose name ends with srl/sa/pfa/ii, across all companies, ignoring ACLs and record rules. The guard added for ACTIONS-004 (`check_cleanup_access()`) was applied only to the attachment/message cleanup methods. The raw update also bypasses the ORM, so stored dependents such as `complete_name` and the cache are not refreshed.
- **Evidence:** source inspection of both methods and of their callers (cron `cron_normalize_company_names`, settings toggle, tests); no RPC call executed.
- **Impact:** Any internal user can rename company partners of companies they cannot access (the change is a deterministic suffix normalization, not arbitrary text). Display names can stay stale until recomputed.
- **Suggested fix:** Make the batch method private (or `@api.private`) and require system/cleanup-administrator rights in the public entry point before the SQL, as done for ACTIONS-004; update through the ORM or invalidate/recompute `complete_name`.
- **Validation needed:** RPC call by a non-administrator rejected with no rename; cron user and administrator still allowed; `complete_name` updated after normalization.
