## Choosing the customers to remind

1. Open the customer (**Invoicing > Customers > Customers**).
2. Tick **Send followup e-mails**, under the **Tags** field. The box must be on the
   same contact that appears on the invoice, not on its parent company.

![Followup box on the customer](static/description/01_partener_bifa_followup.png)

## Defining a followup

1. Go to **Invoicing > Configuration > Followups** and click **New**. You need
   accounting manager rights and the **Followup manager** group.
2. Fill in the **Name** and the **Code**, then choose the **Date field to use**
   (invoice date or due date), the **Comparator** and the **Days from**:
   - **Equal** processes only the invoices whose date plus the offset is today;
     a day on which the scheduled action does not run is lost.
   - **Greater or equal** processes every invoice from that day on, so the
     reminder is repeated daily.
3. Choose the **Mail template** (required) and, under **Invoices placeholder**, the
   HTML of one invoice row, with `$number`, `$payment_term_id`, `$date_invoice`,
   `$date_due`, `$amount_untaxed`, `$amount_tax`, `$amount_total`, `$amount_due`
   and `$currency`.
4. Set the options: **Only open invoices**, **Parse refund invoices**, **Use
   customer currency** and the **Amount margin**.

![Followup form](static/description/03_formular_followup.png)

## What happens when it runs

For each active followup and each flagged customer, the module takes the posted
invoices that match the followup, adds up the totals and sends the e-mail built
from the template. Amounts and dates follow the language of the customer.

![E-mail generated for the customer](static/description/05_email_trimis.png)

- If the invoices in the e-mail add up to the margin or less, or to a negative
  amount (credit notes over invoices), no e-mail is sent and a note is posted on
  the customer.
- If a customer cannot be processed, a note says that the followup failed and
  why; the other customers are processed normally.
- The e-mails appear in **Settings > Technical > Email > Emails** until they are
  sent; with **Auto Delete** on the template they are removed afterwards.

![Note posted when the amount is within the margin](static/description/06_nota_marja.png)

A reminder does not replace a formal notice of non-payment.
