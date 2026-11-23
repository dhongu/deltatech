To use this module with an external service like **cron-job.org**, follow these steps:

### 1. Global Configuration
1. Go to **Settings > General Settings** and search for **Cron Monitor**.
2. Generate or set a **Global Webhook Token**. You can use the **Generate Token** button to create a secure UUID.
3. **Save** the settings.

### 2. Configure the Cron Job
1. Go to **Settings > Technical > Automation > Scheduled Actions**.
2. Open the cron job you want to trigger externally.
3. In the **Webhook Configuration** tab:
   - Check **Enable Webhook**.
   - Provide a unique **Webhook Code** (e.g., `sync_partners`).
   - Copy the generated **Webhook URL** (it already contains the global token for convenience).

### 3. Setup on cron-job.org
1. Log in to your [cron-job.org](https://cron-job.org) account.
2. Click **Create cronjob**.
3. **URL**: Paste the Webhook URL from Odoo.
4. **Request Method**: Select `GET` or `POST`.
5. **Schedule**: Set your desired interval.

### 4. Authentication Options (choose ONE)
You can authenticate using the global token in three ways:

- **URL Parameter (Recommended)**: Append `?token=YOUR_TOKEN` to the URL.
- **HTTP Header**: Add `X-Access-Token: YOUR_TOKEN`.
- **JSON Body (POST only)**: Send a JSON with a `token` key (requires `Content-Type: application/json`).

**Example of JSON Body:**
```json
{
  "token": "YOUR_GLOBAL_TOKEN_HERE"
}
```

### 5. Verification
You can test the integration by clicking **Run now** on cron-job.org or by visiting the Webhook URL in your browser.
Odoo will return a JSON response. In case of success, the HTTP status is `200 OK`. In case of error, one of these HTTP status codes is returned:

- `401`: the token is missing or wrong (`Invalid token`).
- `404`: the webhook code does not exist or the webhook is disabled (`Invalid webhook code or disabled`).
- `409`: the cron job is already running (`Job already running`); it is not started a second time.
- `500`: the cron job failed (`Cron execution failed`).

**Success Response:**

- `status`: `success`
- `job_name`: The name of the cron job.
- `execution_time`: How long it took to run.
- `timestamp`: The time of execution.

**Error Response:**

- `status`: `error`
- `message`: Description of the error (e.g., `Invalid token`, `Job already running`, `Cron execution failed`).
- For `409` and `500`, also `job_name`, `execution_time` and `timestamp`.

The response never contains the exception text of a failed cron job: check the Odoo server log for the error details.
