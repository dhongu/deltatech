# Known bugs

Other bugs of this module are tracked as GitHub issues (label `19.0`).

## ACTIONS-006 — P2: Company-name normalization is public and rewrites partners without authorization

- **Status:** Open. Found on 2026-10-03 while fixing ACTIONS-004.
- **Location:** models/res_partner.py, `batch_normalize_company_names()` and `cron_normalize_company_names()`.
- **Trigger:** An internal user calls `res.partner.batch_normalize_company_names` (or `cron_normalize_company_names`) through ORM/RPC.
- **Actual behavior:** Both methods are public and perform no caller check: the batch method runs a raw SQL `UPDATE res_partner SET name = ...` on every company partner whose name ends with srl/sa/pfa/ii, across all companies, ignoring ACLs and record rules. The guard added for ACTIONS-004 (`check_cleanup_access()`) was applied only to the attachment/message cleanup methods. The raw update also bypasses the ORM, so stored dependents such as `complete_name` and the cache are not refreshed.
- **Evidence:** source inspection of both methods and of their callers (cron `cron_normalize_company_names`, settings toggle, tests); no RPC call executed.
- **Impact:** Any internal user can rename company partners of companies they cannot access (the change is a deterministic suffix normalization, not arbitrary text). Display names can stay stale until recomputed.
- **Suggested fix:** Make the batch method private (or `@api.private`) and require system/cleanup-administrator rights in the public entry point before the SQL, as done for ACTIONS-004; update through the ORM or invalidate/recompute `complete_name`.
- **Validation needed:** RPC call by a non-administrator rejected with no rename; cron user and administrator still allowed; `complete_name` updated after normalization.
