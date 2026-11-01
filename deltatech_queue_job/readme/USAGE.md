**External Job Processor Configuration**

To process jobs every minute using an external service like [cron-job.org](https://cron-job.org):

1.  **Configure API Key**: Go to `Job Queue` -> `Settings`. You can generate a secure key using the **Generate Key** button.
2.  **Configure Batch Settings**: (Optional) Adjust **Batch Size** (default 20) and **Max Seconds** (default 50) directly in the same settings screen, then **Save**.

    ![Settings, Queue Job section: the Queue Job Processor block with the API Key, the Generate Key button (1), Batch Size 20 (2) and Max Seconds 50 (3), followed by the cron-job.org setup instructions](static/description/en/01_setari_procesor_extern.png)

3.  **Setup cron-job.org**:

    *   **URL**: `https://your-odoo-domain.com/api/v1/queue/process`
    *   **Method**: POST
    *   **Schedule**: Every minute (`* * * * *`)
    *   **Headers**: `Content-Type: application/json`
    *   **Body**:

    ```json
    {
      "jsonrpc": "2.0",
      "params": {
        "api_key": "YOUR_SECURE_KEY_HERE"
      }
    }
    ```

**API Endpoints**

### Process Queue (External)
**POST** `/api/v1/queue/process`

Parameters:

- `api_key` (required): Authentication key
- `batch_size` (optional): Maximum number of jobs to process (default: 20)
- `max_seconds` (optional): Maximum processing time in seconds (default: 50)

Response: the result is wrapped twice, so the fields below are in `result` -> `result` of the
JSON body. The HTTP status is always 200, even for an invalid key or an error, which are reported in
the body as `"status": "error"`; alerts based on the HTTP status in the external service will not
catch them.

```json
{
  "status": "success",
  "processed": 15,
  "done": 13,
  "failed": 1,
  "postponed": 1,
  "pending_count": 10,
  "time_elapsed": 12.34,
  "timestamp": "2026-03-18 04:40:00"
}
```

`processed` counts the jobs attempted in this call: `done` finished, `failed` ended in
the failed state and `postponed` were put back to pending for a retry.

### Queue Statistics (External)

**POST** `/api/v1/queue/stats`, with the same body and API key. It only counts the jobs and processes
nothing, which makes it a safe way to check the key before enabling the processing call.

![The POST request to api/v1/queue/stats with the Content-Type header and the JSON body with the API key, and the Odoo response wrapped twice in result, with status success and stats: pending 2, started 0, done 0, failed 1, total 4](static/description/en/02_raspuns_api.png)

**Manual Processing**

Open `Job Queue` -> `Queue` -> `Jobs`. The list header has the module's buttons:

- **Cron Trigger** (1): activates the queue cron and starts it within a few seconds;
- **Process Background** (2): processes one batch right away in a separate thread, without blocking the web interface (fixed batch of up to 20 jobs in 50 seconds, not the values from the settings);
- **Process** (3): shown once at least one job is selected; it only acts when at least one selected job is pending, and then starts the queue cron, which processes the whole queue, not only the selected jobs. Restart a failed job first with **Requeue Job**.

The same buttons are on the job form header (there, **Process Background** is labelled **Process (Thread)**).

![Jobs list: four jobs, pending, enqueued and one failed in red, the first row selected; the header shows Cron Trigger (1), Process Background (2) and Process (3)](static/description/en/03_lista_joburi.png)

After **Cron Trigger**, a notification confirms the request: green when the run is scheduled, yellow "CRON Trigger already exists" when a run is already scheduled, red "No CRON Trigger found" when the queue cron is missing.

![Jobs list after Cron Trigger: the green notification in the top right corner confirms that the operation will run in the background](static/description/en/04_declansare_cron.png)
