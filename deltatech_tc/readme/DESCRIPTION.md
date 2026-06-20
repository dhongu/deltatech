Base module for **Terrabit Connect** — the lightweight native agent that runs on
a workstation and bridges Odoo with local hardware and services it cannot reach
directly from the cloud: the ANAF token (PKCS#11 / mTLS to SPV), fiscal printers
(Datecs), label printers (Zebra ZPL) and declaration validation (DUKIntegrator).

This module is the **generic foundation** every Terrabit Connect feature builds
on. It does not, by itself, talk to any device — it provides the connection
layer and the job protocol.

**What it gives you**

- **Station registry** (`deltatech.tc.station`) — one record per workstation
  running Terrabit Connect, each with a unique API key, a last-seen timestamp
  and reported metadata (TC version, operating system, enabled features).
- **Outbound job queue** (`deltatech.tc.job`) — Odoo enqueues `pending` jobs;
  the station claims them, executes them locally, and reports back the result
  (`done` / `error`).
- **REST endpoints** authenticated with the `X-Station-Key` header:
  `/tc/heartbeat`, `/tc/poll`, `/tc/result`, `/tc/config/<id>`.

**Cloud model — no inbound ports.** The station always initiates the connection
to Odoo; Odoo never connects back to the workstation. The same agent works with
on-premise and cloud deployments without opening any port on the client side.

**Extensible.** Feature modules add their own job types (`selection_add` on
`job_type`) and turn the station's result into business records by overriding the
`_process_result` hook — keeping the registry, queue and transport in one place.
