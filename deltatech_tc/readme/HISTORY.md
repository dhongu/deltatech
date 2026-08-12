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
