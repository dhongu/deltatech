## Security groups

Assign users to the appropriate group under **Settings → Users & Companies → Users**
(field *Terrabit Connect*):

| Group | Access |
|---|---|
| **User** | Can view stations and jobs (read-only) |
| **Manager** | Full access: create/edit stations, download config, regenerate keys, view job details |

The administrator (`base.user_admin`) is a Manager by default.

Only Managers can access the **Settings → Terrabit Connect** menus and download
`station.conf` files (the endpoint `/tc/config/<id>` checks the Manager group).

## Station registration

Each physical workstation that runs Terrabit Connect needs **one station record**
in Odoo:

1. Go to **Settings → Terrabit Connect → Stations → New**.
2. Set **Name** (identifies the workstation in job logs and notifications).
3. Set **Company** (defaults to the user's company; used for multi-company job routing).
4. Save to generate the **API Key** automatically.

The API key is the credential the agent uses in the `X-Station-Key` HTTP header.
It is displayed masked in the form and visible only to system administrators.

## Station configuration file (`station.conf`)

After registering a station, click **Download config** on the station form.
The downloaded file contains two environment variables consumed by Terrabit Connect:

| Variable | Description |
|---|---|
| `TERRABIT_ODOO_BASE` | Base URL of the Odoo instance (e.g. `https://yourcompany.odoo.com`) |
| `TERRABIT_STATION_KEY` | The station's API key — treat it as a secret |

In Terrabit Connect, import `station.conf` from **Settings → Import config**
(**Setări → Importă config** in the Romanian interface). The values are stored in the active profile of
the workstation (`~/.terrabit-anaf-agent/profiles/<profile>.conf`) and applied
without a restart.

The agent's interface language is set in **Settings → Appearance → Language**:
**Auto** (default) follows the language of the station company's partner, sent by
Odoo in the heartbeat answer (Romanian for `ro_RO`, English otherwise); **Română**
or **English** fix it for the workstation profile (`TERRABIT_LANG=ro` / `en`).
No other network configuration is required: the agent initiates all connections
outbound to Odoo (no inbound port needs to be opened on the client side).

![Terrabit Connect settings: configuration profile Default, active, on firma-demo.odoo.com with a station, and the features ANAF signature and Odoo bridge enabled](static/description/13_tc_app_setari.png)

![Terrabit Connect settings, Odoo connection: Odoo instance firma-demo.odoo.com, the API key masked, browser access and the token / ANAF section](static/description/14_tc_app_conexiune_odoo.png)

## Job polling and heartbeat (workstation side)

The heartbeat runs on its own: once at start-up, then every 300 seconds. **Job
polling is off until you turn it on** in the station profile:

| Variable | Default | Effect |
|---|---|---|
| `TERRABIT_POLL_JOBS` | off | `1` lets the station claim and run jobs from `/tc/poll`. While it is off, jobs queued in Odoo stay `pending` |
| `TERRABIT_POLL_SEC` | 30 | Seconds between `/tc/poll` calls (minimum 5) |

## Queue settings (Odoo side)

System parameters (**Settings → Technical → System Parameters**), all optional:

| Parameter | Default | Effect |
|---|---|---|
| `deltatech_tc.claim_timeout_minutes` | 15 | A claimed job without result after this long counts as lost. `0` turns recovery off |
| `deltatech_tc.max_attempts` | 3 | Offers of a retry-safe job before it fails |
| `deltatech_tc.done_ttl_days` | 30 | Finished jobs older than this are deleted by the hourly cleanup (`0` = keep) |
| `deltatech_tc.done_ttl_hours` | 0 | When set, finished jobs go after this many hours instead (`0` = use the days) |
| `deltatech_tc.pg_done_ttl_hours` | 6 | Finished `pg_query` pages go after this many hours (`0` = like the other jobs) |
| `deltatech_tc.error_ttl_days` | 90 | Same for jobs in error |
| `deltatech_tc.pending_ttl_hours` | 0 | Pending jobs no station picked up expire after this long. `0` = never |

Keep the claim timeout above the longest job you run (a DUKIntegrator validation, a slow
device): a retry-safe job that is still running when it expires is executed twice.

## Hosts reachable by `http_request` (workstation side)

`http_request` jobs are refused unless the target host is allow-listed **on the
workstation**. The list is deliberately not manageable from Odoo: it is the last
line of defence if an Odoo account is compromised.

```
TERRABIT_HTTP_ALLOW=192.168.1.50:8080,unisorter.local
```

Comma-separated `host` or `host:port` entries. An entry without a port allows any
port on that host; with a port, the match is exact. **The default is empty — until
a host is listed there, every `http_request` job comes back as an error.** Keep it
as narrow as the job actually needs.

## Terrabit Connect PostgreSQL (workstation side)

The PostgreSQL agent is a separate Windows service (`tc-postgresql`), installed from
the release zip with `install.ps1`, with its own station and key. Its configuration
lives in `%ProgramData%\Terrabit\tc-postgresql\`:

- `station.conf` downloaded from the station (or `[odoo]` in `config.toml`);
- `config.toml`: one `[profiles.<name>]` per database (host, database, a **read-only**
  user, timeouts, page limits); passwords encrypted with
  `tc-postgresql secret set <profile>` (Windows DPAPI). `allow_sql = true` lets Odoo send
  SQL for the profile (feature `pg_sql:<profile>`): give that database user `SELECT` only,
  only on the schema or tables Odoo needs — its grants are what Odoo can read;
- `queries\<profile>\*.sql` (optional): named queries, for profiles without `allow_sql`.

`tc-postgresql check` verifies the files, the database and the Odoo connection. The
station form then shows **Agent** `tc-postgresql`, the features `postgresql,pg:<profile>`
and the installed queries. The agent updates itself from signed releases.

On the Odoo side, `deltatech_tc.pg_done_ttl_hours` (default 6) sets how long finished
`pg_query` pages are kept: their data is already in the records of the calling module, and a
synchronization reads thousands of them. The former `deltatech_tc.pg_done_ttl_days` still
counts (in days) when only it is set; `0` there, as before, keeps the pages like the other jobs.

The server applies a 60-second throttle on `last_seen` writes to reduce database
load when many stations are polling frequently; online detection remains accurate
within the throttle window.
