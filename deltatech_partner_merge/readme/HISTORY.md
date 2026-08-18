## 19.0.1.0.0 (2026-08-18)

- Add: bulk merge of partners duplicated on the same VAT number, with classification, guards,
  simulation on a rolled-back transaction, and verification against a snapshot taken before the
  merge. Wraps the SQL procedure from `deltatech/scripts/partner_merge/`, validated on a client's
  staging database (575 records merged in three batches, zero discrepancies on invoices, orders,
  deliveries and unreconciled balance).
