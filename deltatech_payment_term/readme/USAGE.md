## Generating a payment term from the Payment Terms form

1. Go to **Accounting > Configuration > Payment Terms**.
2. Open an existing payment term or create a new one.
3. Click the **Create Rate** button in the form header.
4. Fill in the wizard fields:
   - **Name** — label for the payment term.
   - **Type** — choose `Percent` (installments as a percentage of the total) or
     `Fixed Amount` (installments as a fixed monetary value).
   - **Advance** — down-payment amount or percentage due immediately (day 0).
   - **Number of rates** — how many installments follow the advance.
   - **Rate Value** — fixed monetary value per installment (visible only when
     Type = Fixed Amount).
   - **Day of the Month** — calendar day on which each installment falls due
     (e.g. `15` means every 15th of the month).
5. Click **Apply**. The existing lines are replaced with the generated schedule.
   The last line is automatically set to "balance" to absorb any rounding difference.

## Generating a payment term from a Sale Order

1. Open a sale order (**Sales > Orders > Orders**).
2. From the **Action** menu (cog icon), select **Payment Term Rate Wizard**.
3. Complete the wizard as described above and click **Apply**.
   The `Sale in Rates` indicator on the order is updated automatically.

## Generating a payment term from an Invoice

1. Open a customer invoice (**Accounting > Customers > Invoices**).
2. From the **Action** menu, select **Payment Term Rate Wizard**.
3. Complete the wizard and click **Apply**.
   The `In Rates` field on the invoice reflects whether the assigned term has
   more than one installment line.

## Viewing installment entries from an Invoice

On any posted invoice that uses a multi-line payment term, click the **Rates**
smart button (top-right button box) to open the related journal entries for that
payment schedule.

## Viewing installment entries from a Partner

On any partner form, click the **Rates** smart button to see all journal entries
linked to installment payment terms for that partner.
