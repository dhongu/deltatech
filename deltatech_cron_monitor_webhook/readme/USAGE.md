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
If successful, Odoo will return a `200 OK` response with:
- `job_name`: The name of the cron job.
- `execution_time`: How long it took to run.
- `timestamp`: The time of execution.

If it fails, check the Odoo logs or the response message (e.g., `Invalid token`, `Invalid webhook code`).
