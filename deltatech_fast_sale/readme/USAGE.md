## Fast confirmation and invoicing from a sale order

1. Go to **Sales > Orders > Orders** and open or create a sale order.
2. Add the products and quantities you want to sell.
3. Click **Confirm, Deliver and Invoice** (visible when the order is in *Draft* or *Sent*
   state) to:
   - confirm the sale order,
   - automatically validate the delivery using the ordered quantities,
   - open the standard invoice creation wizard.
4. In the invoice wizard, select the invoicing option and click **Create Invoice**.

If the order is already confirmed (state *Sale Order*), use **Deliver and Invoice** to
perform the delivery and open the invoice wizard in a single step.

## Deliver Notice (deferred invoicing)

1. Open a confirmed sale order.
2. Click **Deliver Notice** to validate the delivery and mark it as a notice, without
   immediately creating an invoice.
3. The module navigates to the resulting picking so you can review or print it.

## Invoice from the picking

1. Go to **Inventory > Operations > Transfers** and open a delivery that is in *Done*
   state and is linked to a sale order.
2. Click **Invoice** in the picking form header to open the invoice creation wizard for
   the related sale order.

> **Note:** All three flows verify stock availability before proceeding. If any product
> is not fully available in the warehouse, the action is blocked and an error message is
> displayed.
