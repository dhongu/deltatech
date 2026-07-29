# Changelog

## 18.0.1.3.0

- Fix: `_cron_trigger` debounce actually works now. It used to compare against
  `search(..., limit=1)` with no ordering and no future filter, so it usually
  looked at a stale past trigger and created a new `ir.cron.trigger` on every
  call - measured in production at 4,312 trigger inserts in 13 hours (one per
  queue job creation). A request is now skipped when a pending trigger already
  fires between now and the requested time.
- Fix: calling `_cron_trigger` with a list of ETAs (as the OCA job runner does
  for delayed jobs) built a `('call_at', '=', [...])` domain, spamming the log
  with osv.expression warnings. The ETAs are handled individually, earliest
  first, so the first trigger created debounces the later ones; past ETAs are
  clamped to now.

## 18.0.1.2.0

- When a new job is created, automatically move older jobs left in the
  `failed` state that share the same `identity_key` to `cancelled`. The
  standard deduplication only checks active states
  (pending/enqueued/wait_dependencies), so failed duplicates used to pile up.
  The record and its traceback are kept for diagnostics and the standard
  `autovacuum` cron removes cancelled jobs later based on the channel
  `removal_interval`.
