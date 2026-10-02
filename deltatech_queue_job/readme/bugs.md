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

## QUEUE-002 — P1: Public processor accepts the shipped shared API key

- **Status:** Fixed in 19.0.1.4.3 — `data/ir_config_parameter.xml` no longer ships an API key; `controllers/main.py` `_check_api_key()` treats an empty or placeholder key as "API disabled" and compares with `secrets.compare_digest` in both `/api/v1/queue/process` and `/api/v1/queue/stats`; `migrations/19.0.1.4.3/post-migration.py` deletes the placeholder from existing databases. Installations that kept the default key must generate a new one in Settings. Covered by tests in `tests/test_api_key.py` (no shared key after install, placeholder/empty/wrong key denied on both endpoints, generated key accepted).
- **Location:** data/ir_config_parameter.xml; controllers/main.py, process_queue_jobs()/get_queue_stats().
- **Trigger:** Install the module and leave the API key unchanged.
- **Actual behavior:** Installation creates a fixed nonempty placeholder key shared by every installation. Public endpoints compare against the stored value and accept it without detecting an unconfigured placeholder. The processing endpoint then uses sudo to run pending jobs; stats similarly exposes global queue counts.
- **Evidence:** Manifest loads the parameter XML under noupdate. Exact default value is present in source; authentication only checks equality/compare_digest and nonempty values. No external request or real queue executed.
- **Impact:** Knowledge of public module source is sufficient to authenticate on installations using the default configuration, trigger queued business work and read queue statistics.
- **Suggested fix:** Generate a unique secret or keep the endpoint disabled until an administrator configures a non-placeholder key; reject the shipped placeholder on existing installations.
- **Validation needed:** Fresh installation must reject the shared placeholder; generated unique keys authenticate; absent/invalid keys are denied; upgrades must not preserve an accepted insecure placeholder silently.

## QUEUE-003 — P2: Legacy run_jobs route calls an undefined runner method

- **Status:** Open.
- **Location:** controllers/main.py, run_jobs(), POST /run_jobs.
- **Trigger:** An authenticated caller posts to /run_jobs.
- **Actual behavior:** The controller calls queue.job._run_pending_jobs(), which is not defined by this module or its declared queue_job/queue_job_cron_jobrunner dependencies. The available methods include _job_runner and _api_job_runner instead.
- **Evidence:** Full module source reviewed and searched local Community, Enterprise and addon Python sources for a def _run_pending_jobs; none found. Both local copies of queue_job_cron_jobrunner define _job_runner, not the called name. No live endpoint invoked.
- **Impact:** The route fails with AttributeError rather than processing pending work.
- **Suggested fix:** Remove the obsolete route or delegate to a supported runner with appropriate authorization, limits and response handling.
- **Validation needed:** Authenticated request executes the intended bounded runner and returns an accurate result; unauthorized users cannot trigger global processing.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. QUEUE-001 was fixed on 2026-10-01 with database-backed tests.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **QUEUE-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.
