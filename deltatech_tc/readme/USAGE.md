## Registering a station

1. Go to **Settings → Terrabit Connect → Stations**.
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
6. Copy `station.conf` to the workstation running Terrabit Connect and (re)start
   the agent. It will authenticate with the `X-Station-Key` header on every call.

## Verifying connectivity

Once Terrabit Connect is running with the downloaded config:

1. Open the station form (**Settings → Terrabit Connect → Stations**, click the station).
2. The **Last seen** field updates within the next poll cycle (≤ 30 s by default).
3. Click **Ping** in the header to enqueue a round-trip test job. The job appears
   in the **Jobs** smart button and should reach state `Done` within seconds.
4. Terrabit Connect managers also receive a browser notification when the agent
   sends a manual heartbeat.

## Monitoring jobs

Navigate to **Settings → Terrabit Connect → Jobs** to see all jobs across all
stations. You can filter by state (`Pending`, `Done`, `Error`) or group by
station or job type.

The job list uses colour coding:

- Green row — `Done`
- Red row — `Error` (open the form to read the error detail)
- Muted row — `Claimed` (the station picked it up; result not yet reported)

## Rotating the API key

If a station key is compromised:

1. Open the station form.
2. Click **Regenerate key** and confirm the prompt.
3. Download the updated `station.conf` and deploy it to the workstation.
   Terrabit Connect will fail to authenticate until it is reconfigured with the new key.

## Adding feature modules

This base module does not talk to any device by itself. Install the relevant
Terrabit Connect feature module (e.g. ANAF messages, fiscal printer, Zebra labels,
DUKIntegrator) to activate additional job types. They appear automatically in the
**Type** column of the job list once the feature module is installed.
