# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## CRONWEB-001 — P2: Cron webhook reports success when Odoo returns a failure action

- **Status:** Open.
- **Location:** controllers/webhook_controller.py, trigger_cron(); Odoo base/models/ir_cron.py, method_direct_trigger().
- **Trigger:** Invoke a valid webhook for a cron whose server action raises a business exception.
- **Actual behavior:** Odoo 19 method_direct_trigger() returns an ir.actions.client action tagged display_exception when execution logs contain an exception. The controller ignores this return value and returns HTTP 200 with status success; its except block does not handle this normal return.
- **Evidence:** Inspected the local Odoo 19 implementation and executed the existing controller method with the documented failure-action return. The response remained HTTP 200, status success.
- **Impact:** External cron monitoring misses failed executions and may suppress retries or alerts.
- **Suggested fix:** Inspect the trigger result, treat display_exception as a failure, and return an appropriate error status and sanitized diagnostic.
- **Validation needed:** A successful cron, a cron raising an exception, and an already-running cron; compare webhook status with the actual execution outcome.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
