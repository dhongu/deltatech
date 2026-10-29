## 19.0.1.0.3 (2026-10-29)

- The status endpoint `/cron/webhook/<webhook_code>/status` now requires the global token (HTTP 401 without it), like the trigger endpoint.
- Both endpoints check the token before the webhook code, so an unknown code cannot be told apart from a wrong token.
- A `GET` call of the trigger endpoint no longer fails with HTTP 500 (*read-only transaction*): the route is declared `readonly=False`.

## 19.0.1.0.2 (2026-10-22)

- Odoo Apps banner title: *Cron Monitor Webhook* (was *Cron Webhook Trigger*), the same as the module name.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
