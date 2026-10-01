# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## QUEUE-001 — P3: API runner reports failed jobs as successful processing

- **Status:** Fixed in 19.0.1.4.2. `_api_job_runner()` reads the job state after
  `_process()` and counts `done`, `failed` (state failed, or an exception escaping
  `_process()`) and `postponed` (back to pending for a retry); `processed` is the number
  of attempted jobs. The endpoint response includes `done` and `postponed`. Covered by
  `tests/test_api_runner_counters.py` (success, business failure, retryable failure,
  mixed batch).
- **Priority:** Re-evaluated from P2 to P3 on 2026-10-01: only the counters in the API
  response were wrong; the job states stored in the database were correct.
- **Location:** models/queue_job.py, _api_job_runner(), lines 89–123; queue_job_cron_jobrunner/models/queue_job.py, _process().
- **Trigger:** Run the API queue endpoint with a job whose business method raises an exception.
- **Actual behavior:** The delegated runner catches business exceptions, persists a failed job, and returns normally. The API runner increments processed and leaves failed at zero because it only counts exceptions escaping _process().
- **Evidence:** Inspected the delegated exception handling and executed the existing API method against a job that transitions to failed and returns normally: processed=1, failed=0. Retry postponements also return normally.
- **Impact:** External monitoring receives misleading execution statistics and can miss job failures.
- **Suggested fix:** Determine results from the persisted job state and distinguish attempted jobs, completed jobs, failures, and postponed retries.
- **Validation needed:** One successful job, one business failure, one retryable failure, and a mixed batch; verify API counters against stored states.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. QUEUE-001 was fixed on 2026-10-01 with database-backed tests.
