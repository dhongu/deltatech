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

- **Status:** Open.
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
