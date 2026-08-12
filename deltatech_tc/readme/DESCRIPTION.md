Base module for **Terrabit Connect** — the lightweight native agent that runs on
a workstation and bridges Odoo with local hardware and services it cannot reach
directly from the cloud: the ANAF token (PKCS#11 / mTLS to SPV), fiscal printers
(Datecs), label printers (Zebra ZPL) and declaration validation (DUKIntegrator).

This module is the **generic foundation** every Terrabit Connect feature builds
on: the connection layer, the job protocol, and the one job type that is pure
transport rather than a specific device — an HTTP call inside the customer's
network.

**What it gives you**

- **Station registry** (`deltatech.tc.station`) — one record per workstation
  running Terrabit Connect, each with a unique API key, a last-seen timestamp
  and reported metadata (TC version, operating system, enabled features).
- **Outbound job queue** (`deltatech.tc.job`) — Odoo enqueues `pending` jobs;
  the station claims them, executes them locally, and reports back the result
  (`done` / `error`).
- **REST endpoints** authenticated with the `X-Station-Key` header:
  `/tc/heartbeat`, `/tc/poll`, `/tc/result`, `/tc/config/<id>`.
- **`http_request` job type** — Odoo asks the station to call a device that
  answers only inside the local network (a sorting line, a scale, a PLC, a label
  server) and reports the response back. Queue it with `_tc_enqueue_http()` and
  read the answer with `response_dict()` / `response_json()`.

**Cloud model — no inbound ports.** The station always initiates the connection
to Odoo; Odoo never connects back to the workstation. The same agent works with
on-premise and cloud deployments without opening any port on the client side.

**Extensible.** Feature modules add device-specific job types (`selection_add` on
`job_type`) and turn the station's result into business records by extending the
`_process_result` hook — keeping the registry, queue and transport in one place.

**Security of `http_request` — read this before using it.** The allow-list of
reachable hosts is configured **in the agent, on the workstation**, never from
Odoo. Without that rule, a job saying "call this URL" would let anyone able to
create a job in Odoo reach any address inside the customer's network. Odoo only
validates the shape of the request (scheme, host present, known method); the
decision to actually place the call belongs to the machine sitting in that
network.

Callbacks are restricted to methods whose name starts with **`_tc_`**. The method
name is stored in the database, so without that rule a modified record could call
any ORM method. The prefix also makes "reachable from a job" a property you can
grep for.
