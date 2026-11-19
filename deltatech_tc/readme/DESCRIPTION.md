Base module for **Terrabit Connect** — the lightweight native agent that runs on
a workstation and bridges Odoo with local hardware and services it cannot reach
directly from the cloud: the ANAF token (PKCS#11 / mTLS to SPV), fiscal printers
(Datecs), label printers (Zebra ZPL) and declaration validation (DUKIntegrator).

Terrabit Connect is a desktop application for Windows, macOS and Linux, built
with Tauri (Rust core, the operating system's own web view). Installers and signed
automatic updates are published at:

`https://github.com/dhongu/terrabit-connect-releases/releases/latest`

![Terrabit Connect main window: the TC service running, the Odoo connection and the unlocked token marked Connected, the ANAF / SPV job queue with 2 jobs in progress and 1 error, and the quick actions Open Odoo and Sync SPV](static/description/11_tc_app_principal.png)

![Terrabit Connect job queue: a declaration validation (DUK) in Error, an SPV message sync Pending, a document download Claimed and a finished SPV sync](static/description/12_tc_app_joburi.png)

The agent's interface is in Romanian and English. By default (**Auto**) it follows the
language of the station's company in Odoo; it can also be fixed per workstation profile.

This module is the **generic foundation** every Terrabit Connect feature builds
on: the connection layer, the job protocol, and the one job type that is pure
transport rather than a specific device — an HTTP call inside the customer's
network.

**✨ What it gives you**

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
- **`pg_query` job type** — for the *Terrabit Connect PostgreSQL* agent (a Windows
  service, separate from the desktop app): Odoo asks for one page of a **read-only
  query** on a database in the customer's network (e.g. orders from a local production
  database) — SQL written in the feature module, or a named query installed on the
  station — and receives the rows; the next pages are queued automatically. Queue it
  with `_tc_enqueue_pg_query()` and read the rows with `pg_rows()`.

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

**Security of `pg_query`.** Odoo names a profile (a database configured on the
station, never a host or a user) and sends either SQL or the name of a query file
installed there. SQL is accepted only on profiles where the station allows it
(`allow_sql`). Each page is a single `SELECT` with bound parameters, in a read-only
transaction with a timeout, under a database user that should only be able to read
what Odoo needs: **that user's grants are the boundary** of what Odoo can read.

Callbacks are restricted to methods whose name starts with **`_tc_`**. The method
name is stored in the database, so without that rule a modified record could call
any ORM method. The prefix also makes "reachable from a job" a property you can
grep for.
