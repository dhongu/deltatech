1. Set the system parameter `sequence.mixin.constraint_start_date` (**Settings > Technical > System Parameters**) to the date before which certain accounting operations should be blocked (format `YYYY-MM-DD`).
2. When a user tries to undo the reconciliation of a bank statement line dated before that date, the operation is blocked with an error message asking them to contact their support team.
3. If the parameter is not set, no restriction is applied (default `2000-01-01`).
