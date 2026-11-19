## Registering a station

1. Go to **Settings → Terrabit Connect → Stations**. The list shows, for each station, when it was
   **Last Seen**, its **TC Version** and whether it runs in **Simulation** (highlighted rows).

   ![Terrabit Connect Stations list: Casa 1 Magazin (test) highlighted with Simulation ticked, PC Contabilitate and Server Winarhi (the PostgreSQL agent, version 0.1.0)](static/description/en/01_lista_statii.png)

2. Click **New** and give the station a descriptive name (e.g. `Accounting PC`).
3. Select the company the station belongs to (multi-company installations).
4. Save. An **API Key** is generated automatically and is visible to administrators
   only (shown masked in the form).
5. Click **Download config** (download icon in the header) — Odoo serves a
   pre-filled `station.conf` file containing:
   ```
   TERRABIT_ODOO_BASE=<your Odoo URL>
   TERRABIT_STATION_KEY=<the generated key>
   ```
6. Copy `station.conf` to the workstation and import it in Terrabit Connect
   (**Setări → Importă config**). The agent authenticates with the
   `X-Station-Key` header on every call.

   ![Station form PC Contabilitate: Ping and Download config in the header, Last Seen, TC Version 1.8.2, Operating System Windows 11, Features and Fiscal Driver fiscalwire](static/description/en/02_formular_statie.png)

## Verifying connectivity

Once Terrabit Connect is running with the downloaded config:

1. Open the station form (**Settings → Terrabit Connect → Stations**, click the station).
2. The **Last Seen** field updates at the first heartbeat, sent as soon as the
   agent starts, and then at every heartbeat or job poll.
3. Click **Ping** in the header to enqueue a round-trip test job. The job appears
   in the **Jobs** smart button and reaches state `Done` at the next poll — provided
   job polling is enabled on the workstation (`TERRABIT_POLL_JOBS=1`, see CONFIGURE).
4. Terrabit Connect managers also receive a browser notification when the agent
   sends a manual heartbeat.

## Simulated stations

When Terrabit Connect runs in simulation mode, the station reports at every heartbeat the fiscal
driver `simulated` and the simulated devices: `fiscal` for the cash register and `terminal:<id>` for
each card terminal. The station form then shows a **Simulation** ribbon and a warning listing the
simulated devices; receipts and card payments made through them are not real. The marking comes from
the station: it disappears on its own at the first heartbeat sent without simulated devices.

![Station form Casa 1 Magazin (test): Simulation ribbon, the warning with the simulated devices fiscal,terminal:demo and Fiscal Driver simulated](static/description/en/03_statie_simulata.png)

## Monitoring jobs

Navigate to **Settings → Terrabit Connect → Jobs** to see all jobs across all
stations. You can filter by state (`Pending`, `Claimed`, `Done`, `Error`) or group by
station or job type.

The job list uses colour coding:

- Green row — `Done`
- Red row — `Error` (open the form to read the error detail)
- Muted row — `Claimed` (the station picked it up; result not yet reported)

![Terrabit Connect Jobs list: a Ping Done (green), an HTTP request (LAN) in Error (red), one Claimed (muted), a Ping Pending and three PostgreSQL query (LAN) pages on Server Winarhi, two Done and the third Pending](static/description/en/04_lista_joburi.png)

Open a job to read its **Payload**, **Result** and **Error** tabs.

![An HTTP request (LAN) job in Error, Error tab open with the message returned by the station, Retry button in the header](static/description/en/05_job_eroare.png)

### Lost results and retries

A job whose result never came back (agent restarted, network down between execution and
reply) is handled after the claim timeout (see CONFIGURE):

- **retry-safe jobs** (`ping`, `http_request` with `GET` or `HEAD`) are offered to the
  station again, then fail after the maximum number of attempts;
- **all other jobs** stay `Claimed`, because they may already have run. Find them with the
  **Claimed** filter, check on the device or at ANAF whether the operation happened, and only
  then use **Retry** on the job form (managers only).

**Retry** also puts a job in `Error` back in the queue.

A feature module whose job type only reads can declare it retry-safe:

```python
def _tc_is_retry_safe(self):
    return self.job_type == "sync_messages" or super()._tc_is_retry_safe()
```

## Rotating the API key

If a station key is compromised:

1. Open the station form.
2. Click **Regenerate key** and confirm the prompt.
3. Download the updated `station.conf` and deploy it to the workstation.
   Terrabit Connect will fail to authenticate until it is reconfigured with the new key.

## Staging and other copies of the database

When the database is copied and neutralized (an odoo.sh staging or development branch, or
`odoo-bin neutralize`), every station of the copy gets a **new key**, so the agents of
production never serve the copy and an agent set up for the copy can not authenticate on
production. Jobs that were still **Pending** or **Claimed** are closed in **Error** instead of
being run a second time. To test on the copy, download `station.conf` from the copy and use it
on a test station (for the PostgreSQL agent: a `[connections.staging]` entry).

## Calling a device on the local network

Queue the call from a feature module:

```python
station = self.env["deltatech.tc.station"].search([("company_id", "=", self.env.company.id)], limit=1)
self.env["deltatech.tc.job"]._tc_enqueue_http(
    station,
    "http://192.168.1.50/api/Lines/1/Lots",
    headers={"X-API-KEY": self.api_key},
    timeout=30,
    callback=(self, "_tc_apply_lots"),
)
```

Handle the response on the record that asked for it:

```python
def _tc_apply_lots(self, job):
    response = job.response_dict()
    if response.get("status") != 200:
        raise UserError(self.env._("The device answered %(code)s.", code=response.get("status")))
    for payload in job.response_json() or []:
        ...
```

The callback method **must** start with `_tc_` — see DESCRIPTION. Before the first
job can succeed, the target host has to be allow-listed on the workstation (see
CONFIGURE).

**The call is asynchronous.** It runs when the station next polls, not when the
job is created. Interactive buttons must therefore show a pending state and let
the result arrive later; do not queue a job and read its result in the same
transaction.

## Reading a PostgreSQL database in the local network

Install the *Terrabit Connect PostgreSQL* agent on a server that reaches the database
(its own station, not the one of the desktop app), with `allow_sql = true` on the profile,
and queue pages from a feature module; the SQL lives in the module:

```python
ORDERS_SINCE = """
    SELECT codunic, nume, datatrecutinprod
      FROM winarhi.comenzi
     WHERE datatrecutinprod >= %(since)s
       AND (%(after)s::bigint IS NULL OR codunic > %(after)s)
     ORDER BY codunic
"""

station = self.env["deltatech.tc.station"]._tc_find("pg:winarhi")
if not station._tc_has_pg_sql("winarhi"):
    raise UserError(self.env._("The Winarhi station does not accept SQL from Odoo (allow_sql)."))
self.env["deltatech.tc.job"]._tc_enqueue_pg_query(
    station,
    "winarhi",
    sql=ORDERS_SINCE,
    key="codunic",
    params={"since": "2026-11-01 00:00:00"},
    page_size=500,
    callback=(self, "_tc_receive_orders"),
)
```

`%(name)s` parameters are bound by the station, never pasted into the SQL; PostgreSQL infers
their types, so add a cast where it cannot (`%(after)s::bigint IS NULL`). With `key`, the SQL
must page on that column with `%(after)s`. On a profile without `allow_sql`, name a query file
installed in its `queries\<profile>\` folder instead (`_tc_enqueue_pg_query(station, "winarhi",
"orders_since", params=...)`, checked with `_tc_has_pg_query`).

The station form then shows the agent and the installed queries:

![Station Server Winarhi: Agent tc-postgresql (1), Features postgresql,pg:winarhi and PostgreSQL queries winarhi: articles, offers_since, orders_since (2)](static/description/en/07_statie_postgresql.png)

The callback runs once per page, and once more if a page fails:

```python
def _tc_receive_orders(self, job):
    if job.state == "error":
        self.message_post(body=job.pg_error().get("message"))
        return
    for row in job.pg_rows():
        ...  # idempotent: a page may arrive twice after a lost result
```

The next page is queued after the callback returns; if it raises, the page is marked
**Error** and **Retry** takes the chain up from that page. `numeric` values arrive as
text (no precision lost), dates and timestamps as ISO text.

![Job #6 PostgreSQL query (LAN) on Server Winarhi, Done, Result tab (2): columns cod_mag, denumire, pret and the rows of the page, prices as text (41.2500)](static/description/en/06_pg_query_pagina.png)

## Adding feature modules

This base module does not talk to any device by itself. Install the relevant
Terrabit Connect feature module (e.g. ANAF messages, fiscal printer, Zebra labels,
DUKIntegrator) to activate additional job types. They appear automatically in the
**Job Type** column of the job list once the feature module is installed.
