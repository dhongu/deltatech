This module provides a simple and secure solution to trigger Odoo cron jobs via webhooks.

### Key Features:
- **Webhook Activation per Cron**: Each scheduled action can be configured to allow external triggering.
- **Unique Webhook Code**: Generate a unique code for each cron to build a dedicated endpoint URL.
- **HMAC Security**: Protection via HMAC-SHA256 signature using a configurable master secret key.
- **Dedicated Endpoints**:
  - Trigger: `/cron/webhook/<webhook_code>` (POST)
  - Status: `/cron/webhook/<webhook_code>/status` (GET)
- **Easy Configuration**: Global settings allow enabling/disabling signature verification and defining the master key.

### Integration:
It is ideal for integration with external monitoring and scheduling platforms such as **cron-job.org**, **healthchecks.io**, or **EasyCron**, allowing better control over when jobs run, independent of the internal Odoo scheduler.
