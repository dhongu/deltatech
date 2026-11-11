## 18.0.1.0.3 (2026-11-11)

- The neutralization script (`data/neutralize.sql`) set `iap_account.sms_secret` to `false`, but the column is `varchar`, so PostgreSQL rejected the statement and neutralizing a restored database failed with *Error neutralizing database (deltatech_sms)*, which blocked restoring a production backup on a staging branch. It now sets the column to `NULL`.
