# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## BUSINESS-001 — P1: Test report rows reuse the process-step ID across test runs

- **Status:** Open.
- **Location:** report/business_process_test_report.py, `_select()`.
- **Trigger:** Test the same process step in two test runs.
- **Actual behavior:** The query selects `bps.id AS id` although each row represents a distinct `business_process_step_test` record. Two runs of the same step therefore share the ORM record ID.
- **Evidence:** Executed the actual extracted SQL with SQLite tables representing two runs: both report IDs are 7, while process_step_test_id values are 100 and 101, with passed and failed results respectively. This verifies SQL identity only; no Odoo database execution.
- **Impact:** ORM identity/cache and list keys cannot distinguish separate test results; record reads and list rendering can show ambiguous or repeated data. Aggregate SQL may still count both rows.
- **Suggested fix:** Use the unique step-test row ID (`bpst.id`) for this report model.
- **Validation needed:** Two runs of the same step with different results; assert unique report IDs and correct list, direct read and grouping behavior.

## BUSINESS-002 — P1: Reports and Open Issue omit company authorization rules

- **Status:** Fixed in 19.0.1.9.5 — the two SQL reports expose `company_id` (the process company) and `security/security.xml` adds global multi-company rules on `business.process.report`, `business.process.test.report`, `business.open.issue`, `business.migration` and `business.migration.test` (the migrations through `project_id.company_id`). Covered by tests in `tests/test_company_rules.py` (Business Admin and End User limited to one company, report company field, Open Issue read/write, migrations, user with both companies).
- **Location:** security/security.xml; security/ir.model.access.csv; both report Python models; models/business_issue.py.
- **Trigger:** A business user accesses the reports, or an internal user accesses business.open.issue, with one company enabled.
- **Actual behavior:** The source process/test/issue models have global company rules, but the separate SQL report models and business.open.issue do not. Their group visibility rules admit unrestricted processes irrespective of company; Business Admin bypasses even that visibility restriction. SQL joins do not apply the source model's ORM rules, and classical inheritance of business.issue does not transfer its model-specific ir.rule records.
- **Evidence:** Complete security declarations provide company rules only for project, process, test, step, step-test, development and business.issue. Report queries have no company predicate; Open Issue has separate base.group_user read/write/create/unlink ACLs. The auxiliary business.migration and business.migration.test models likewise have base.group_user read ACLs without company rules; their project/migration references do not propagate project authorization.
- **Impact:** Reports expose process/test data from other companies. Open Issue records can also be read or edited outside the intended company scope, subject to process visibility. Additional deployment-specific rules can mitigate the gap.
- **Suggested fix:** Add global company rules on both report models through process_id.company_id and on business.open.issue through company_id.
- **Validation needed:** Two-company ORM tests for reports and Open Issue, including Business Admin, with only one company enabled. No Odoo database tests executed.

## Review limitations

All eligible module source has been manually read. Findings are supported by inspected source and isolated reproductions. This does not establish database execution, rendered UI correctness or production deployment.

## BUSINESS-003 — P1: Public acceptance-test creation bypasses process access checks

- **Status:** Fixed in 19.0.1.9.4 — `start_user_acceptance_test()` requires the Business End User group (or superuser) and calls `check_access("read")` on the processes before creating the test as superuser; the created tests are returned in the caller's environment. Covered by tests in `tests/test_acceptance_test_access.py` (visible process, hidden process, process of a disabled company, internal user without a business group, the "Start Test" smart button).
- **Location:** models/business_process.py, `start_user_acceptance_test()` and `_start_test()`.
- **Trigger:** Invoke the public method through ORM/RPC with the ID of a process hidden by company or allowed_user_ids rules.
- **Actual behavior:** The method immediately calls `self.sudo()._start_test("user_acceptance")`. It neither checks a caller group nor calls `check_access()` before elevation. The helper reads the process and its steps, searches tests and creates a test with step records as superuser.
- **Evidence:** Executed the actual extracted public method with a mock whose read check would reject access: it calls sudo then test creation, without invoking the check. Compared with `_check_state_access()`, which explicitly verifies caller group and read access before sudo. No live RPC/database call performed.
- **Impact:** A caller can create tests against inaccessible processes, circumventing the module's company and process visibility restrictions; the returned sudo record can also be used by custom callers to access test data.
- **Suggested fix:** Check caller authorization and source process access before elevation, and return records in the original caller environment.
- **Validation needed:** RPC tests with a hidden process and a process in a disabled company; verify rejection and absence of new tests/steps.

## BUSINESS-004 — P2: Batch development approval uses singleton notification logic

- **Status:** Open; source verified 2026-10-02.
- **Location:** models/business_development.py, `write()`.
- **Trigger:** Approve multiple development records with a single write, for projects with a project manager.
- **Actual behavior:** After `super().write(vals)`, the override accesses `self.project_id.project_manager_id`, posts a message on the full recordset and passes `self.id` to send_mail, without iterating developments. `message_post()` and `self.id` require one record.
- **Evidence:** Inspected the override: there is no record loop or ensure_one restriction on write; stock ORM supports batch writes. Approval of a multi-record set reaching notification therefore raises Expected singleton and rolls back.
- **Impact:** Batch approvals and imports updating approvals fail, even when all records belong to one project. Single-record approval works.
- **Suggested fix:** Iterate approved developments and send each notification using its record ID and project manager.
- **Validation needed:** Two-development approval in one project and across projects, including a project without a manager. No database tests executed.

## BUSINESS-005 — P2: Git sources with matching repository basenames share one checkout

- **Status:** Open; source verified 2026-10-02.
- **Location:** models/business_process_library.py, `_repo_local_name()`, `_sync_git_repo()`, `_iter_process_sources()`.
- **Trigger:** Configure two Git URLs with different owners/hosts but the same final repository name, such as org-a/processes.git and org-b/processes.git.
- **Actual behavior:** Both derive the cache key processes. The second synchronization detects the first checkout's .git directory and pulls its existing origin, without checking or switching to the requested URL. Source discovery then also suppresses the second source because its label is already seen.
- **Evidence:** Executed the actual extracted cache-key method: both URLs return processes. Inspected the pull command and duplicate-label filter; no network or Git synchronization executed.
- **Impact:** The second source's processes are unavailable, and logs can attribute the first source's checkout to the second URL. Commands may also use authentication arguments intended for a different configured URL.
- **Suggested fix:** Derive the directory/source identity from the complete repository URL and verify the checkout origin before pulling.
- **Validation needed:** Two local Git repositories with identical basenames and different process content; confirm distinct caches and sources without external network.

## BUSINESS-006 — P2: Reimport ignores exported process durations

- **Status:** Open; source verified 2026-10-02.
- **Location:** wizard/import_business_process.py, `do_import()`, existing-process write branch.
- **Trigger:** Export a process with Include Durations, change its durations, then import it into a project where the same process code already exists.
- **Actual behavior:** The import reads all duration values and passes them when creating a new process, but the existing-process write omits configuration_duration, instructing_duration, data_migration_duration and testing_duration. Other process metadata is updated.
- **Evidence:** Compared export duration keys, import parsing, and create/write dictionaries. Both branches are selected by the same code/project lookup; only the create branch includes durations.
- **Impact:** Reimport silently leaves old effort estimates and derived totals, despite the export explicitly including the new durations.
- **Suggested fix:** Apply the four duration inputs in the update branch when include_durations is true; preserve existing durations when false.
- **Validation needed:** Reimport with included durations enabled/disabled, asserting all four inputs and their computed total. No database tests executed.

## BUSINESS-007 — P2: Library autodiscovery misreads the settings Boolean

- **Status:** Open; source verified 2026-10-02.
- **Location:** models/res_config_settings.py, process_library_autodiscover; models/business_process_library.py, `_iter_process_sources()`.
- **Trigger:** Save the Discover processes from all modules setting with no whitelist configured.
- **Actual behavior:** The library enables discovery only when get_param(..., "1") equals "1". Odoo settings pass the Boolean directly to set_param: True becomes the Char value "True", which fails this comparison. False deletes the parameter, making the library use its enabled default "1".
- **Evidence:** Inspected local base res.config.settings.set_values() and ir.config_parameter.set_param(). The reader evaluates "True" == "1" as false and the missing-parameter fallback "1" == "1" as true.
- **Impact:** Saving the enabled option can empty module discovery, while disabling it can enable discovery. Git sources are independent; a whitelist takes precedence.
- **Suggested fix:** Use consistent Boolean serialization/parsing and a persisted disabled representation when the desired default is enabled.
- **Validation needed:** Save enabled and disabled settings, reopen settings and inspect available sources with no whitelist and with a whitelist. No database tests executed.

## BUSINESS-008 — P2: Rejected-development filter targets the wrong field

- **Status:** Open; source verified 2026-10-02.
- **Location:** views/business_development_view.xml, is_rejected filter.
- **Trigger:** Set a development's approval to Rejected and activate the Rejected search filter.
- **Actual behavior:** The filter searches state = rejected. Development state accepts draft, specification, development, test and production; rejected is an approved selection value.
- **Evidence:** Compared the active XML filter domain with both selections in models/business_development.py. A valid rejected development has approved = rejected and a different state, so it cannot match.
- **Impact:** The filter omits rejected developments and gives an empty result despite existing rejected approvals.
- **Suggested fix:** Filter on approved = rejected.
- **Validation needed:** Approved and rejected developments in different lifecycle states; confirm only rejected approvals appear. No browser/database tests executed.

## BUSINESS-009 — P3: Start Internal/Integration Test server actions elevate with sudo without an explicit caller check

- **Status:** Open. Found on 2026-10-03 while fixing BUSINESS-003.
- **Location:** views/business_process_view.xml, `action_start_internal_test` and `action_start_integration_test` (`action = records.sudo().start_internal_test()` / `records.sudo().start_integration_test()`); models/business_process.py, `start_internal_test()`, `start_integration_test()` and `_start_test()`.
- **Trigger:** Run "Start Integration Test" (or "Start Internal Test") from the Action menu of a business process.
- **Actual behavior:** The server action code switches to superuser before calling the test-creation methods, which themselves have no group or `check_access()` call. This is the pattern fixed for the acceptance test in BUSINESS-003 (`start_user_acceptance_test()` now checks the group and process read access before `sudo()`), but the two sibling actions were left unchanged. The only remaining gate is the core one in `ir.actions.server._can_execute_action_on_records()` (no `group_ids`, so write access on `business.process` and on the selected records is required).
- **Evidence:** source inspection of the view, the model methods and Odoo 19 `ir.actions.server.run()` / `_can_execute_action_on_records()`; no reproduction on a database.
- **Impact:** Limited: only users with write access on the processes reach the code, but the test, its steps and step tests are created as superuser, bypassing the ACLs and company rules of `business.process.test`. Conversely, a process responsible (read-only on `business.process`) cannot use these actions at all, although the acceptance test is available to business end users. The behavior is inconsistent with BUSINESS-003.
- **Suggested fix:** Drop `sudo()` from the action code and apply the BUSINESS-003 pattern in the methods (explicit group check, `check_access("read")`, controlled `sudo()` returning records in the caller environment), or restrict the actions with `group_ids`.
- **Validation needed:** Process manager, process responsible, end user and a user of another company running both actions; assert rejection or creation according to the intended roles and that no test is created on an inaccessible process.

## BUSINESS-010 — P3: "Abandon" has no server-side state or role check

- **Status:** Open. Found on 2026-10-03 while fixing BUSINESS-003.
- **Location:** models/business_process.py, `button_abandon()`; views/business_process_view.xml, the Abandon button.
- **Trigger:** Call `button_abandon` through RPC on a process in state production (or already abandoned), as a user with write access on `business.process` who is not a system administrator.
- **Actual behavior:** The method only does `self.write({"state": "abandoned"})`. The restrictions exist only in the view (`groups="base.group_system"`, `invisible="state in ('abandoned','production')"`). The other transition buttons go through `_check_state_access()` (role and access check) and `button_end_test()` additionally validates the process tests; `button_abandon()` does neither.
- **Evidence:** source inspection of the transition methods and of the form buttons; no reproduction on a database.
- **Impact:** A process in production can be abandoned through RPC by a non-administrator with write rights, which the UI forbids. The risk is limited because the same users can write the state field directly and the change can be reverted with Reset to Draft.
- **Suggested fix:** Enforce the intended role and refuse the transition from `production`/`abandoned` in the method itself, consistently with `_check_state_access()`.
- **Validation needed:** Abandon from each state, as administrator, process manager and process responsible, through RPC.

## BUSINESS-011 — P1: Creating an Open Issue fails with MissingError (mail template bound to business.issue)

- **Status:** Fixed in 19.0.1.9.6 — new mail template `email_template_open_issue_submitted` bound to `business.open.issue`; `send_issue_mail()` takes the template from `_get_issue_submitted_template()` (overridden in `business.open.issue`) and skips any template whose model is not the record model. The patch workaround in `tests/test_company_rules.py` was removed. Covered by tests in `tests/test_open_issue_mail.py` (creation with and without a `business.issue` sharing the id, mail rendered on the Open Issue and sent to the project manager, Business Issue mail unchanged). Priority P1 confirmed.
- **Location:** models/business_issue.py, `create()` and `send_issue_mail()`; data/email_templates.xml, `email_template_issue_submitted` (`model_id` = `model_business_issue`); `business.open.issue` inherits `business.issue` by classical inheritance (`_name` + `_inherit`).
- **Trigger:** Create a `business.open.issue` record (UI or RPC).
- **Actual behavior:** `create()` calls `send_issue_mail()`, which renders `email_template_issue_submitted` with `send_mail(item.id)`. The template model is `business.issue`, so the ID of the Open Issue is browsed in the `business.issue` table: when no business issue has that ID the rendering raises MissingError and the creation is rolled back; when one exists, the mail is rendered and sent with the data of that unrelated business issue.
- **Evidence:** source inspection of the create/send path and of the template definition; observed as MissingError while writing the Open Issue tests for BUSINESS-002.
- **Impact:** Open Issues cannot be created on a database where the IDs do not collide; otherwise the project manager receives a notification about the wrong issue (possibly of another project or company).
- **Suggested fix:** Use a template per model (one bound to `business.open.issue`), or skip/override `send_issue_mail()` in `business.open.issue`; never pass an ID of one model to a template of another.
- **Validation needed:** Create an Open Issue on a database with and without a `business.issue` sharing the same ID; assert the creation succeeds and the mail (if any) refers to the Open Issue.

## BUSINESS-012 — P3: Import/export and workflow tests are not tagged post_install

- **Status:** Open. Found on 2026-10-03 while fixing BUSINESS-003 and BUSINESS-002.
- **Location:** tests/test_wizard_process_io.py (`TestBusinessProcessImportExport`), tests/test_workflow_fixes.py (`TestWorkflowFixes`); most of the other test files in tests/ lack the tag as well.
- **Trigger:** Run the module tests on a database where `account` / `website_sale` are installed after this module (for example a shared test database with the whole suite).
- **Actual behavior:** The tests run at install time, before modules installed later have added their NOT NULL columns with defaults to the ORM, and fail with `NotNullViolation: null value in column "autopost_bills" of relation "res_partner"` (setUpClass of `TestWorkflowFixes`, `test_import_creates_missing_masterdata`).
- **Evidence:** test logs of the BUSINESS-003/BUSINESS-002 runs; the files use `TransactionCase` without `@tagged("post_install", "-at_install")`.
- **Impact:** Test noise only: false failures on shared databases hide real regressions. No runtime impact.
- **Suggested fix:** Tag the test classes `@tagged("post_install", "-at_install")`, as `test_acceptance_test_access.py` and `test_company_rules.py` already are.
- **Validation needed:** Run the module tests on a database with account and website_sale installed; assert no NotNullViolation.

## BUSINESS-013 — P2: Open Issues get no code (no ir.sequence for business.open.issue)

- **Status:** Open. Found on 2026-10-03 while fixing BUSINESS-011.
- **Location:** models/business_issue.py, `BusinessIssue.create()` (inherited by `business.open.issue`), which sets `vals["code"] = self.env["ir.sequence"].next_by_code(self._name)`; data/ir_sequence_data.xml defines sequences only for `business.project`, `business.process`, `business.process.step`, `business.issue` and `business.development`.
- **Trigger:** Create a `business.open.issue` record without an explicit `code` (UI or RPC).
- **Actual behavior:** `next_by_code("business.open.issue")` finds no sequence and returns False, so `code` stays empty; `display_name` drops the `[code]` prefix and Open Issues cannot be told apart or searched by code.
- **Evidence:** source inspection of `create()` and of all data/*.xml files (no `ir.sequence` with code `business.open.issue`); no database reproduction.
- **Impact:** Open Issues have no identifier; no data loss, the record is still created. Existing Open Issues stay without a code.
- **Suggested fix:** Add a `sequence_open_issue` record (code `business.open.issue`, own prefix, e.g. `OI`) to data/ir_sequence_data.xml; since the file is `noupdate="1"`, a migration script or a separate non-noupdate record is needed for existing databases, optionally filling the code of existing Open Issues.
- **Validation needed:** Create an Open Issue on an updated database; assert `code` is set from the new sequence and differs from the `business.issue` numbering.

## BUSINESS-014 — P3: Open Issue submission mail template is not translated

- **Status:** Open. Found on 2026-10-03 while fixing BUSINESS-011.
- **Location:** data/email_templates.xml, `email_template_open_issue_submitted` (added in 19.0.1.9.6); i18n/deltatech_business_process.pot and i18n/ro.po have no entries for it (subject "Open Issue Submitted", body_html).
- **Trigger:** An Open Issue is created and the project manager's language is Romanian.
- **Actual behavior:** The mail is sent in English, while the `business.issue` template (`email_template_issue_submitted`) has Romanian translations.
- **Evidence:** source inspection: no `email_template_open_issue_submitted` / "Open Issue Submitted" occurrence in the .pot or ro.po; no database reproduction.
- **Impact:** Cosmetic: untranslated notification for Romanian users.
- **Suggested fix:** Regenerate the .pot and add the Romanian translations of the subject and body to i18n/ro.po.
- **Validation needed:** Load ro_RO, create an Open Issue for a project whose manager uses Romanian; assert the mail subject and body are in Romanian.
