### External Job Processor Configuration

To process jobs every minute using an external service like [cron-job.org](https://cron-job.org):

1.  **Configure API Key**: Set a secure key in `Settings` -> `Technical` -> `System Parameters` for the key `queue_job_processor.api_key`.
2.  **Configure Batch Settings**: (Optional) Adjust `queue_job_processor.batch_size` (default 20) and `queue_job_processor.max_seconds` (default 50).
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

### API Endpoints

#### Process Queue (External)
**POST** `/api/v1/queue/process`

Parameters:
- `api_key` (required): Authentication key
- `batch_size` (optional): Maximum number of jobs to process (default: 20)
- `max_seconds` (optional): Maximum processing time in seconds (default: 50)

Response:
```json
{
  "status": "success",
  "processed": 15,
  "failed": 0,
  "pending_count": 10,
  "time_elapsed": 12.34,
  "timestamp": "2026-03-18 04:40:00"
}
```

### Manual Processing
You can manually trigger job processing from the Queue Job list view using the **Process** button (internal cron trigger) or **Process (Thread)** (API-style runner in a new thread), or trigger a background execution using **Cron Trigger**.
