## 19.0.1.0.19 (2026-11-03)

- Fixed: the transfer list showed two empty columns on deliveries (the hidden operation type and
  the supplier invoice number); they are now hidden as columns.
- Fixed: a return (or a copy) of an invoiced transfer kept the invoice of the original transfer, so
  it was not left to invoice; the invoice link is no longer copied.
- Tests for returns, refunds and partial vendor bills.

## 19.0.1.0.18 (2026-11-03)

- Description aligned with the code: the to-invoice flag is set when the picking is validated, and storable lines of invoices created from pickings are locked.
- Usage guide headings as bold lines, so the module README can be generated with the usage section.

## 19.0.1.0.17 (2026-11-03)

- Fixed: the Force Invoice Order checkbox on the sale order was shown without its label, in the row
  of the fiscal position; it is now a field of the Invoicing group. Its Romanian label is
  „Facturează cantitatea comandată".
- Consultant sheet (`readme/FISA_CONSULTANT.md`) and usage page, with RO and EN screenshots generated
  by `tests/test_screenshots.py`.

## 19.0.1.0.16 (2026-10-17)

- Fixed: the To invoice flag of a transfer was decided by a single invoice line, so a fully invoiced
  product could clear the flag of a transfer with another product only partly invoiced, and two
  partial invoices covering the whole delivery left the transfer to invoice. The flag is now derived
  from all the done moves of the transfer and the cumulative invoiced quantity of each order line
  (non-cancelled invoices minus refunds); the quantity not invoiced yet is attributed to the most
  recent transfers (PICKINV-002). Resetting a cancelled invoice to draft links its transfers again.
- Fixed: a batch with a partially invoiced transfer was reported as invoiced and the batch Invoice
  action left that transfer out; it is now kept, so the rest can be invoiced (PICKINV-003).

## 19.0.1.0.15 (2026-10-16)

- Fixed: invoicing several selected batch transfers stopped after the first batch; the not yet
  invoiced transfers of all the selected batches are now invoiced together (delivery and receipt
  batches cannot be mixed).
- Fixed: a batch without transfers was reported as invoiced.
- Fixed: the Invoice button on the batch form was shown on batches that were not done or were already
  invoiced (`and` instead of `or` in its visibility condition).

## 19.0.1.0.14 (2026-10-07)

- Fixed: the Create Purchase Invoices action could bill an already billed receipt again, with the full
  receipt quantity, and moved the receipt's invoice link to the new bill. The billed quantity is now
  capped at what is still to bill on the purchase order line (received minus billed on non-cancelled
  bills), and receipts with nothing left to bill are refused with an error (PICKINV-004). After a bill
  is cancelled, the receipt can be billed again.

## 19.0.1.0.13 (2026-10-06)

- Summary in English, as the Apps Store requires, the same as the banner; support address.

## 19.0.1.0.12 (2026-10-03)

- Fixed: invoicing from transfers copied the stock move quantity into the invoice line without unit
  conversion. A purchase line of 1 Dozen received as 12 Units was billed as 12 Dozen (12 times the
  amount), and a partial delivery of 12 Units on a 2 Dozen sale line was invoiced as 2 Dozen. Move
  quantities are now converted from the move unit to the order line unit before summing and before
  the remaining-quantity cap (PICKINV-001). Invoice quantities change whenever the order unit differs
  from the stock move unit.
- Declared the missing `purchase_stock` dependency: the transfer form uses `stock.picking.purchase_id`,
  added by `purchase_stock`, so a standalone install failed with `Field "purchase_id" does not exist`.
  No change on existing databases, where `purchase_stock` is auto-installed with `purchase` and `stock`.

## 19.0.1.0.11 (2026-09-29)

- Own module icon, instead of the generic gears it had.
