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
6. Copy `station.conf` to the workstation and import it in Terrabit Connect
   (**Setări → Importă config**). The agent authenticates with the
   `X-Station-Key` header on every call.

## Verifying connectivity

Once Terrabit Connect is running with the downloaded config:

1. Open the station form (**Settings → Terrabit Connect → Stations**, click the station).
2. The **Last seen** field updates at the first heartbeat, sent as soon as the
   agent starts, and then at every heartbeat or job poll.
3. Click **Ping** in the header to enqueue a round-trip test job. The job appears
   in the **Jobs** smart button and reaches state `Done` at the next poll — provided
   job polling is enabled on the workstation (`TERRABIT_POLL_JOBS=1`, see CONFIGURE).
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

## Adding feature modules

This base module does not talk to any device by itself. Install the relevant
Terrabit Connect feature module (e.g. ANAF messages, fiscal printer, Zebra labels,
DUKIntegrator) to activate additional job types. They appear automatically in the
**Type** column of the job list once the feature module is installed.
