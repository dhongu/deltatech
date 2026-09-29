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

In Terrabit Connect, import `station.conf` from **Setări → Importă config** (the
agent's interface is in Romanian). The values are stored in the active profile of
the workstation (`~/.terrabit-anaf-agent/profiles/<profile>.conf`) and applied
without a restart.
No other network configuration is required: the agent initiates all connections
outbound to Odoo (no inbound port needs to be opened on the client side).

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
| `deltatech_tc.done_ttl_days` | 30 | Finished jobs older than this are deleted by the daily cleanup (`0` = keep) |
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

The server applies a 60-second throttle on `last_seen` writes to reduce database
load when many stations are polling frequently; online detection remains accurate
within the throttle window.
