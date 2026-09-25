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
