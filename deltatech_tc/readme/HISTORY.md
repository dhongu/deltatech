## 20.0.1.4.1 (2026-11-19)

- Documentation, examples, tests and screenshots use a neutral `erp` profile and a `Server ERP`
  station instead of a customer's names; no functional change.

## 20.0.1.4.0 (2026-11-19)

- `pg_query` accepts **SQL written in the calling module** (`_tc_enqueue_pg_query(station, profile,
  sql=..., key=...)`), with psycopg2-style `%(name)s` parameters bound by the station and `key`
  for keyset pagination (`%(after)s` in the SQL). The station runs it only on a profile with
  `allow_sql` (Terrabit Connect PostgreSQL 0.2.0, feature `pg_sql:<profile>`;
  `station._tc_has_pg_sql(profile)`). The read-only database user of the profile bounds what
  Odoo can read. Named query files on the station remain available.
- The station form lists a profile without query files by its name.

## 20.0.1.3.1 (2026-11-19)

- Database neutralization (odoo.sh staging / development copies, `odoo-bin neutralize`) gives
  every station a new random key, so production's agents never serve the copy and an agent set
  up for the copy can not authenticate on production. Jobs still pending or claimed are closed
  in error instead of being run a second time.

## 20.0.1.3.0 (2026-11-18)

- New job type **`pg_query`** for the *Terrabit Connect PostgreSQL* agent
  (`terrabit-solutions/terrabit-connect-postgresql`), a Windows service that runs **named,
  read-only** queries on a PostgreSQL database in the customer's network. Odoo sends only the
  profile name, the query name and its parameters, never SQL; the `.sql` files live on the
  station. One page per job, keyset pagination (`after` = key of the last row).
- `_tc_enqueue_pg_query()` queues the first page; with `follow` the next page is queued
  automatically once the callback of the current one succeeded. The callback also receives a
  failed page (`job.state == "error"`, `job.pg_error()` gives `{code, message}`), including one
  failed after the retry limit. `pg_rows()` returns the rows of a page. Pages are retry-safe.
- Heartbeat: the agent name (`agent`) and the installed queries (`pg_profiles`) are stored on
  the station (**Agent**, **PostgreSQL queries**). `_tc_find(feature)` returns the company's
  active station announcing a feature (whole element, e.g. `pg:erp`);
  `_tc_has_pg_query(profile, query)` checks an installed query.
- Daily cleanup: finished `pg_query` pages are deleted after 3 days
  (`deltatech_tc.pg_done_ttl_days`).

## 20.0.1.2.7 (2026-11-15)

- The heartbeat answer (`/tc/heartbeat`) carries `lang`, the language of the station company's
  partner (`en_US` when it has none). Terrabit Connect set to **Auto** uses it for its
  interface: Romanian for `ro_*`, English otherwise. Older agents ignore the key.
- Docs: the agent's interface is available in Romanian and English.
- Port of 19.0.1.2.7 (dhongu/deltatech#4186).

## 20.0.1.2.6 (2026-11-15)

- Docs: screenshots of the Terrabit Connect app (main window, job queue, settings) in the
  description, the configuration section and the consultant sheet. The download address is now written out in
  full, because the Odoo Apps page turns links in the description into plain text. No code
  change.

## 20.0.1.2.5 (2026-11-15)

- Port of 19.0.1.2.5.
- The station shows the fiscal driver and the devices Terrabit Connect simulates (from the
  heartbeat): a **Simulation** ribbon and a warning on the form, highlighted rows in the list.
- Consultant sheet (`readme/FISA_CONSULTANT.md`), usage with screenshots, and the test that
  generates them (`tests/test_screenshots.py`).

## 20.0.1.2.4 (2026-10-11)

- Docs: emoji symbols added to the bold headings of the module description, for a uniform look on the Odoo Apps page. No code change.

## 20.0.1.2.3 (2026-10-04)

- TC-001 (security): downloading a station config (`/tc/config/<station_id>`) read the station as superuser, so a Terrabit Connect manager limited to company A could download the config, including the API key, of a station of company B by changing the id in the URL. The station is now looked up with the manager's own rights: a station of a company the manager does not have access to answers 404, like a missing one; the API key itself is still read as superuser.
- Port of 19.0.1.2.3 (dhongu/deltatech#3116). In 20 the 404 answers of the endpoint are raised (`raise request.not_found()`) instead of returned: Odoo 20 logs a warning for an endpoint that returns an HTTPException.
- Tests: the invalid queue setting test expects the warning `get_int()` logs for a non-numeric value (an unexpected warning fails the CI run). No functional change.

## 20.0.1.2.2 (2026-09-30)

- New Apps Store banner, with the module icon, and the job retry and queue cleanup feature.

## 20.0.1.2.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.2.0 (2026-09-29)

- **Atomic claim.** `/tc/poll` locks the rows it hands out (`FOR UPDATE SKIP LOCKED`). Two
  simultaneous polls with the same key (a second workstation installed by copying the
  profile) could both receive, and run, the same job.
- **Lost results.** A job claimed longer than `deltatech_tc.claim_timeout_minutes` (15)
  without a result used to stay `claimed` for ever. A retry-safe job (`ping`, an
  `http_request` with `GET`/`HEAD`; extend `_tc_is_retry_safe()` for other read-only types)
  is offered again, up to `deltatech_tc.max_attempts` (3), then fails. Any other job is left
  `claimed`: it may have run, and its late result is still accepted.
- **Retry** button on the job (managers): error or stuck jobs go back to `pending`. No
  `sudo`, so a read-only user cannot re-run a job over RPC either.
- **Daily cleanup** cron: `done` jobs older than 30 days and `error` jobs older than 90 are
  deleted; pending jobs can expire after `deltatech_tc.pending_ttl_hours` (off by default).
- New field `attempt_count`, new **Claimed** filter.

## 19.0.1.1.3 (2026-09-29)

- The endpoints accept only the `X-Station-Key` header. The legacy `X-Agent-Key` fallback
  is removed: every Terrabit Connect release since 1.5 sends `X-Station-Key`.
- Documentation describes the Tauri desktop agent (Windows, macOS, Linux) and where to
  download it, how to import `station.conf`, and that job polling must be enabled on the
  workstation (`TERRABIT_POLL_JOBS=1`). `TERRABIT_HEARTBEAT_SEC` is no longer documented:
  the heartbeat interval is fixed at 300 seconds.
- New `readme/ROADMAP.md`.

## 19.0.1.1.2 (2026-09-25)

- Security: `/tc/poll` returns only the jobs queued for the calling station. It used to
  claim every pending job of the station's company and reassign it, so one station could
  take (and read the payload of) jobs meant for another workstation.
- Security: `/tc/result` accepts a result only for a job in state `claimed` (409 otherwise).
  A finished job could be re-posted, overwriting its result and replaying the callback.
- `/tc/poll` caps `limit` to 1–50; `/tc/result` rejects a non-integer `job_id` with 400.

## 19.0.1.1.1 (2026-08-15)

- Fix: added the missing `bus` dependency. The manual heartbeat notification
  uses `self.env["bus.bus"]._sendone()`, which is defined in `bus`. The module
  only worked when another addon in the same database brought `bus` in.

## 19.0.1.1.0 (2026-08-11)

- **New job type `http_request`** — the station performs an HTTP call inside the customer's local
  network on Odoo's behalf, so cloud-hosted Odoo can reach devices that answer only on the LAN
  (sorting lines, scales, PLCs, label servers) without a VPN, a fixed IP or an inbound port.
- `_tc_enqueue_http()` helper, `response_dict()` / `response_json()` readers, payload validation
  (scheme, host, HTTP method).
- Callbacks: `_process_result` now invokes `(record, method)` registered on the job. Only methods
  prefixed `_tc_` may be called, checked both when queuing and at call time.
- The allow-list of reachable hosts is configured on the workstation
  (`TERRABIT_HTTP_ALLOW`), never from Odoo.

## 19.0.1.0.0

- Station registry, outbound job queue, REST endpoints (`/tc/heartbeat`, `/tc/poll`, `/tc/result`,
  `/tc/config/<id>`) and the `ping` job type.
