Lets you receive goods in stock starting from the vendor bill: when a bill has
storable products that are not on any purchase order, the module creates the
purchase order for you, and the receipt is validated when the bill is posted.

**Purchase order created from the bill.** When you click **Confirm** on a vendor
bill, every line with a storable product that is not linked to a purchase order
is put on a purchase order: a new order with the vendor, the bill date, the bill
reference, the fiscal position and the currency of the bill, or, when the other
lines of the bill already come from a single purchase order, that order. The
order lines take the product, unit, quantity, unit price, discount and taxes of
the bill lines, and the bill lines are linked to them. A note with a link to the
new order is posted on the bill.

**Confirm the order, then post the bill.** A new order is created as a request
for quotation, so posting stops with the message *Please confirm purchase order
before posting invoice*. Open the order, click **Confirm Order**, then click
**Confirm** on the bill again.

**Receipt validated with the bill.** When the bill is posted, the receipts of the
orders created from bills are validated with the ordered quantities, and the
stock moves are dated on the order date (the bill date).

**Negative quantities on purchase orders.** A purchase order line with a
negative quantity of a storable product creates a separate return transfer to
the vendor when the order is confirmed, with the return operation type of the
receipt. Increasing the negative quantity later adds only the difference to the
return.

## Limitations

- The automatic purchase order and receipt work only for vendor bills; vendor
  credit notes are not processed when posted.
- Lines added to a regular purchase order (one not created from a bill) are not
  received automatically.
- The purchase order is not confirmed automatically.
