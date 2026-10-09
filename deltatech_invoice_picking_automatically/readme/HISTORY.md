## 19.0.0.0.6 (2026-10-09)

- Each automatic invoicing in the cron now runs in its own savepoint. An error
  (posting validation or database error) rolls back only that picking's work, so
  no orphan draft invoice is left behind, the picking is marked as failed and
  logged, and the other pickings of the run are still invoiced.

## 19.0.0.0.5 (2026-09-29)

- Own module icon, instead of the generic gears it had.
