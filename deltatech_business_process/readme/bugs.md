# Known bugs

Other bugs of this module are tracked as GitHub issues (label `19.0`).

## BUSINESS-009 — P3: Start Internal/Integration Test server actions elevate with sudo without an explicit caller check

- **Status:** Open. Found on 2026-10-03 while fixing BUSINESS-003.
- **Location:** views/business_process_view.xml, `action_start_internal_test` and `action_start_integration_test` (`action = records.sudo().start_internal_test()` / `records.sudo().start_integration_test()`); models/business_process.py, `start_internal_test()`, `start_integration_test()` and `_start_test()`.
- **Trigger:** Run "Start Integration Test" (or "Start Internal Test") from the Action menu of a business process.
- **Actual behavior:** The server action code switches to superuser before calling the test-creation methods, which themselves have no group or `check_access()` call. This is the pattern fixed for the acceptance test in BUSINESS-003 (`start_user_acceptance_test()` now checks the group and process read access before `sudo()`), but the two sibling actions were left unchanged. The only remaining gate is the core one in `ir.actions.server._can_execute_action_on_records()` (no `group_ids`, so write access on `business.process` and on the selected records is required).
- **Evidence:** source inspection of the view, the model methods and Odoo 19 `ir.actions.server.run()` / `_can_execute_action_on_records()`; no reproduction on a database.
- **Impact:** Limited: only users with write access on the processes reach the code, but the test, its steps and step tests are created as superuser, bypassing the ACLs and company rules of `business.process.test`. Conversely, a process responsible (read-only on `business.process`) cannot use these actions at all, although the acceptance test is available to business end users. The behavior is inconsistent with BUSINESS-003.
- **Suggested fix:** Drop `sudo()` from the action code and apply the BUSINESS-003 pattern in the methods (explicit group check, `check_access("read")`, controlled `sudo()` returning records in the caller environment), or restrict the actions with `group_ids`.
- **Validation needed:** Process manager, process responsible, end user and a user of another company running both actions; assert rejection or creation according to the intended roles and that no test is created on an inaccessible process.
