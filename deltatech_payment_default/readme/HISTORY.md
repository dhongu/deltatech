## 20.0.1.0.0 (2026-11-14)

- Migration to Odoo 20.0, no functional change. The tests no longer write `is_company` on the
  partner: on Odoo 20 it is computed, and the commercial partner of a contact comes from
  `parent_id`.

## 19.0.1.0.0 (2026-10-26)

- New module: **Set as default** checkbox in the payment register wizard
  stores the payment method (and journal) on the commercial partner,
  separately for receipts and payments, and proposes it for the next
  payments, including for invoices addressed to a contact and invoices
  already open without a preferred payment method.
