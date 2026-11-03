The accountant often needs to see how the money collected from customers in a period splits between
the cash and bank journals and the invoice journals it settled. This module builds that view for
customer receipts, on demand, from a small wizard.

**Customer receipts by journal**: the report takes the customer payments (incoming, partner type
customer) in state **Paid** or **Reconciled**, dated in the chosen period and booked in the chosen
cash and bank journals. Draft, cancelled and rejected payments and vendor payments are left out.

**Filter wizard**: **Start Date** and **End Date** (both default to today) and **Incasari**, the cash
and bank journals to include (all of them by default).

**Pivot, list and form views**: **Show** opens the report in pivot view, with the **Payment Journal**
on rows, the **Invoice Journal** on columns and the amount as measure. The list and form views show
for each payment the date, customer, amount, payment journal, invoice journal and payment method.
The invoice journal is the journal of the invoice the payment is reconciled with.

**Card payment method on bank journals**: if a payment method with the code `card` exists, it can
be used only on bank journals, once per journal.

## Usage

Go to **Invoicing > Accounting > Payment Report** (accounting Administrator group only), set the period and the
journals, then click **Show**.

## Limitations

- Only customer receipts are reported; vendor payments and outgoing payments are not.
- The amounts are in the currency of each payment and the pivot adds them up without conversion.
- A payment reconciled with invoices from several journals is reported under one of them only.
- The company of the wizard does not filter the payments; the journals selected decide the scope.
