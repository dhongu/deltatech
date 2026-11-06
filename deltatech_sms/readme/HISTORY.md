## 20.0.1.0.4 (2026-11-06)

- Fix: the reason returned by the provider for a refused SMS was lost. The response was
  returned under the key `error`, while Odoo reads `failure_reason`; the reason now
  reaches the SMS notification of the message.

## 20.0.1.0.3 (2026-11-03)

- Description rewritten from the code: the custom endpoint with
  {number}/{content} is gone; only the 4Pay and Wapi providers are supported.
- Configuration path (In-App Purchase Accounts on Odoo 20) and limitations
  (no delivery reports, fixed endpoints) documented.

## 19.0.1.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
