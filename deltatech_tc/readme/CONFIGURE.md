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

Place `station.conf` on the workstation and restart Terrabit Connect. No other
network configuration is required: the agent initiates all connections outbound
to Odoo (no inbound port needs to be opened on the client side).

## Tuning poll and heartbeat cadence

The following environment variables can be set on the workstation side to tune
timing (Terrabit Connect reads them at startup):

| Variable | Default | Effect |
|---|---|---|
| `TERRABIT_POLL_SEC` | 30 | Seconds between `/tc/poll` calls |
| `TERRABIT_HEARTBEAT_SEC` | 300 | Seconds between automatic heartbeats |

The server applies a 60-second throttle on `last_seen` writes to reduce database
load when many stations are polling frequently; online detection remains accurate
within the throttle window.
