Adds a **Set as default** checkbox to the payment register wizard
(**Register Payment** on invoices and bills). When it is checked, the
payment method used (and therefore its journal) is stored on the partner
and proposed again for the next payments.

Features:

- Stores the choice in the standard partner fields **Payment Method**
  (Sales & Purchase tab): one for receipts (customer invoices) and one for
  payments (vendor bills), per company. No new fields on the partner.
- The default is written on the commercial partner (the company), so all
  its contacts use it. New invoices addressed to a contact take the
  company default when the contact has none.
- Invoices that were already open when the default was set get it in the
  wizard too, as long as they have no preferred payment method of their
  own. A payment method set explicitly on the invoice still wins.
- Every change is logged in the partner chatter (who, which method,
  which company).
- The checkbox is shown only for a single partner and only to users who
  can edit partners (**Contact Creation**) and invoices.
