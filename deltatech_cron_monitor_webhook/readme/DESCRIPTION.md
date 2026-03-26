This module provides a simple and secure solution to trigger Odoo cron jobs via webhooks using a global access token.

### Key Features:
- **Webhook Activation per Cron**: Each scheduled action can be configured to allow external triggering.
- **Unique Webhook Code**: Define a unique code for each cron to build a dedicated endpoint URL.
- **Global Token Security**: Protection via a global access token (Bearer or Parameter) instead of complex HMAC signatures.
- **Dedicated Endpoints**:
  - Trigger: `/cron/webhook/<webhook_code>` (POST/GET)
  - Status: `/cron/webhook/<webhook_code>/status` (GET)
- **Easy Configuration**: A single global token manages access for all enabled webhooks, simplifying integration with external services.

### Integration:
It is ideal for integration with external monitoring and scheduling platforms such as **cron-job.org**, **healthchecks.io**, or **EasyCron**, allowing better control over when jobs run, independent of the internal Odoo scheduler.
