# Changelog

## 18.0.1.2.0

- When a new job is created, automatically move older jobs left in the
  `failed` state that share the same `identity_key` to `cancelled`. The
  standard deduplication only checks active states
  (pending/enqueued/wait_dependencies), so failed duplicates used to pile up.
  The record and its traceback are kept for diagnostics and the standard
  `autovacuum` cron removes cancelled jobs later based on the channel
  `removal_interval`.
