# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## ACTIONS-001 — P1: Contact merge detaches contacts that it does not merge

- **Status:** Open.
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

- **Status:** Open; source verified 2026-10-02.
- **Location:** models/account_move.py, `cron_clean_xml_attachments()`.
- **Trigger:** Multiple invoices have XML attachments with a common name, or another document has an attachment with the same name.
- **Actual behavior:** SQL groups by name across account.move XML attachments, but the subsequent ORM search restricts only name and optional age. It omits res_model, res_id and mimetype. EDI protection uses the invoice obtained from attachments[0].res_id; all attachments linked to other invoices remain in the deletion candidates.
- **Evidence:** Inspected the SQL grouping, ORM domain and single-invoice edi_document_ids subtraction. Deletion applies sudo.unlink to the resulting wider set; no destructive reproduction performed.
- **Impact:** Same-name attachments on unrelated models or valid XMLs on other invoices can be selected for deletion. This is not a per-invoice duplicate check. Other installed unlink protections may block individual cases.
- **Suggested fix:** Identify duplicates per invoice and document content/type; retain the original model/type restrictions and protect each invoice's EDI links.
- **Validation needed:** Shared filenames across invoices/models, different content under one filename, and EDI links for every invoice; assert only genuine duplicates are removed.

## ACTIONS-004 — P1: Public attachment cleanup bypasses caller authorization

- **Status:** Open; source verified 2026-10-02.
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
