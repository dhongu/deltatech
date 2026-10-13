1. Create a customer invoice in the journal with *Delivery from invoice* and add the products.
2. Click **Confirm**. The sale order is created and confirmed, the delivery is validated and a note on the
   invoice links to the order.
3. When a product does not have enough stock, the invoice stays in draft and the message shows the available
   and the requested quantity.
4. To take goods back on the same invoice, add the product with a negative quantity: a return is validated
   together with the delivery.

With `l10n_ro_stock_account_date` installed, the stock accounting entries of the delivery take the accounting
date of the invoice, so the sale (707) and the cost of the goods sold (607) fall in the same period.

Limits:

- Use this journal only when the goods leave on the invoice date. Goods delivered earlier, especially in a
  previous month, are recorded at the delivery date (418) and invoiced afterwards, from the delivery.
- A negative line on the invoice must refer to the original invoice (number and date). The goods returned this way
  enter the stock at the current cost of the product, not at the cost of the original delivery: for an exact
  reversal of the cost, return them from the original delivery and issue a credit note.
