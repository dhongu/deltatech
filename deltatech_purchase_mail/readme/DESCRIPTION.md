When several requests for quotation or purchase orders go to the same vendor, sending
them one by one means one email per order. This module sends them together, in a
single email to that vendor, with an Excel summary of all the lines and the PDF of
each order.

**One email for several orders**: select the orders in the list view of
**Purchase > Orders > Requests for Quotation** or **Purchase > Orders > Purchase
Orders** and choose **Actions > Send Email**. The standard email composer opens with
the vendor as recipient.

**XLSX summary**: the email carries an Excel file with one row per order line:
order reference, product code, description, quantity and unit price without taxes.

**PDF of each order**: the standard purchase order PDF of every selected order is
attached to the same email.

**Trace on every order**: only when the email is actually sent, each order gets a note
with the email body, the summary and its own PDF, and the requests for quotation still
in draft move to **RFQ Sent**. Closing the composer without sending changes nothing.

**Email template**: the text comes from the template **Purchase Orders: Send with
XLSX**, editable in **Settings > Technical > Email > Templates** (developer mode).

## Limitations

- All the selected orders must have the same vendor, and the vendor must have an email
  address. Otherwise the action stops with the message "You must select exactly one
  vendor to send the email to.", also when the only problem is the missing email.
- The vendor's address is the only recipient filled in; other recipients are added by
  hand in the composer.
- In the XLSX summary, a reference, product code or description that starts with "="
  is written as a formula, not as text.
