## Registering a card payment

1. On a sales order, on a posted customer invoice, or from
   **Accounting > Customers > Card Payment on Customer**, press
   **Card Payment**.
2. Check the amount (it is proposed with the amount due; a partial payment is
   allowed), the date and the terminal (selected automatically for the user).
3. On a sales order choose how the payment is invoiced:
   - **Pay an issued invoice**, when the order already has an open invoice;
   - **Issue a down payment invoice** (default when nothing is invoiced): the
     down payment invoice is created from the order, posted and paid;
   - **No invoice** (managers only): the amount stays as customer credit. Use
     it only when the delivery is invoiced in the same VAT period as the
     payment (month, or quarter for quarterly filers); otherwise the VAT on the
     down payment, due when it is received, is reported late. In Romania the
     down payment invoice is due at the latest on the 15th of the following
     month.
4. Press **Register**. The payment is posted (5125 = 4111) and the receipt
   appears in **Accounting > Customers > Expected Receipts** as *Pending
   Settlement*.

## Settling the bank transfer

1. Import the bank statement of the card account.
2. On the grouped statement line, use **Action > Card Settlement** (or
   **Accounting > Accounting > Card Settlement** and select the line).
3. Press **Search**. The module looks for pending card payments of the
   statement line's journal, from the window set on the terminal:
   - one exact combination: it is ticked; press **Settle**;
   - several combinations: the *Combination* column shows which receipt belongs
     to which; tick the right group and press **Settle**;
   - no exact combination: the message shows how much is missing; usually a
     card payment was not registered or the bank fee is included.
4. The ticked payments are reconciled with the statement line on the suspense
   account and the receipts become *Settled*.

The bank fee is expected on its own statement line (627 = 5121). If the bank
transfers the net amount (fee withheld), no exact combination exists: tick the
receipts manually and book the fee as the remaining difference on the suspense
account (627 = 5125) in the standard bank reconciliation.

## Follow-up

- The **Late** filter shows card payments still pending after the alert
  threshold of their terminal.
- A receipt registered by mistake is cancelled with **Cancel Receipt**
  (managers): the payment is cancelled too. A down payment invoice issued for
  it stays posted, with its VAT, and is reversed with a credit note. A settled
  receipt, or one from a closed period (VAT return already filed), is corrected
  by a reversal in accounting, not by cancelling.
