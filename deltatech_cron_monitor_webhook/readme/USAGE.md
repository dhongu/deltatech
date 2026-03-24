To use this module with an external service like **cron-job.org**, follow these steps:

### 1. Global Configuration
1. Go to **Settings > General Settings** and search for **Cron Monitor** (or scroll to the Cron Monitor section).
2. Enable **Verify Webhook Signature** if you want to use HMAC security (recommended).
3. Generate or set a **Master Webhook Secret**. You can use the **Generate Key** button to create a secure random key.
4. **Save** the settings.

### 2. Configure the Cron Job
1. Go to **Settings > Technical > Automation > Scheduled Actions**.
2. Open the cron job you want to trigger externally.
3. In the **Webhook Configuration** tab:
   - Check **Enable Webhook**.
   - Provide a unique **Webhook Code** (e.g., `sync_partners`).
   - Copy the generated **Webhook URL**.

### 3. Setup on cron-job.org
1. Log in to your [cron-job.org](https://cron-job.org) account.
2. Click **Create cronjob**.
3. **URL**: Paste the Webhook URL from Odoo.
4. **Request Method**: Select `POST`.
5. **Schedule**: Set your desired interval.
6. **Headers**:
   - Add `Content-Type: application/json`.
   - If signature verification is enabled, add `X-Signature: YOUR_CALCULATED_SIGNATURE`.
7. **Body** (if signature verification is enabled):
   Provide a JSON with a `timestamp`.
   ```json
   {
     "timestamp": "2024-03-24T12:00:00Z"
   }
   ```

### 4. HMAC Signature Calculation
The signature is calculated using **HMAC-SHA256** with:
- **Message**: Concatenation of `webhook_code` and `timestamp` (e.g., `sync_partners2024-03-24T12:00:00Z`).
- **Secret**: The **Master Webhook Secret** configured in Odoo.

**Example of signature generation (Python):**
```python
import hmac
import hashlib

webhook_code = "sync_partners"
timestamp = "2024-03-24T12:00:00Z"
secret = "your_master_secret_here"

message = f"{webhook_code}{timestamp}"
signature = hmac.new(
    secret.encode(),
    message.encode(),
    hashlib.sha256
).hexdigest()

print(f"X-Signature: {signature}")
```

### 5. Verification
You can test the integration by clicking **Run now** on cron-job.org. If successful, Odoo will return a `200 OK` response with execution details. If it fails, check the Odoo logs for details (e.g., invalid signature or execution error).
