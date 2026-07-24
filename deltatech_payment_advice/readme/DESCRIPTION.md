# Deltatech Payment Advice

This module adds a **Payment Advice** (remittance advice) report on batch
payments. It is the document a payer sends to its suppliers to notify them that
one or more of their invoices have been settled through a bank payment order.

Starting from a batch payment, the report groups the payments by supplier and
produces one advice per supplier, listing the settled bills together with the
amount actually allocated to each one.

## Key Features

- Adds a **Payment Advice** PDF report on `account.batch.payment`.
- Groups the batch payments by supplier — one advice document per supplier.
- Lists the settled vendor bills (number, date, due date) with the amount
  effectively allocated to each bill, computed from the payment reconciliation
  (partial payments are reported correctly).
- Renders each supplier's advice in that supplier's own language.

## Requirements

- Depends on `account_batch_payment` (Odoo Enterprise batch payments).
- Payments must be reconciled with their vendor bills for the advice to list
  the settled invoices.
