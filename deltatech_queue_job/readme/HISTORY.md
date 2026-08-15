# Changelog

## 19.0.1.4.0

- Fix: jobs cancelled through the dependency chain are now removed by the
  autovacuum cron. `Job.cancel_dependent_jobs()` cancels them with a raw SQL
  `UPDATE queue_job SET state = ...` that writes nothing else, while
  `queue.job.autovacuum()` selects what to delete by `date_done` or
  `date_cancelled` — so a job cancelled that way was never collected, however
  long it sat there. A production instance had 189.644 such jobs, 53% of the
  table and all of them `marketplace_write` cancelled in chains during
  marketplace sync. `models/job_patch.py` stamps `date_cancelled` right after
  the chain cancellation (the query itself cannot be fixed at the source: it is
  shared with `enqueue_waiting()`, where a cancellation date would be wrong).
- Imp: `autovacuum()` also removes terminal jobs left with no completion date at
  all, keyed on `date_created` and on the same per-channel `removal_interval`.
  This collects what piled up before the fix; jobs in `failed` state are never
  touched, they are the only ones worth keeping for diagnosis.

## 19.0.1.3.0

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
  clamped to now. Ported from 18.0 (18.0.1.3.0).

## 19.0.1.2.0

- When a new job is created, automatically move older jobs left in the
  `failed` state that share the same `identity_key` to `cancelled`. The
  standard deduplication only checks active states
  (pending/enqueued/wait_dependencies), so failed duplicates used to pile up.
  The record and its traceback are kept for diagnostics and the standard
  `autovacuum` cron removes cancelled jobs later based on the channel
  `removal_interval`.
