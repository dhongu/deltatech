Before you start, see *Configuration* to enable the payment providers you use.

Scenario: a customer ordered 2 pcs × 500 + VAT (1,210.00 in total) and chose to pay by bank
transfer. The money has arrived in the bank account, and the sales operator confirms the payment on
the order.

**Step 1 — Check the order with the payment pending**

Go to **Sales → Orders → Quotations** (or **Orders**) and open the order.

Under **Payment Terms** the module adds:

- **Payment** — the amount collected so far (here 0.00) and, next to it, the payment provider
  (**Bank Transfer**);
- **Payment Status** — **Pending**: the customer chose bank transfer, but the money has not been
  confirmed yet.

Colors make it easy to read: green = **Paid**, orange = **Partially paid / Pending / Initiated /
Authorized**, red = **Cancelled**, gray = **Without payment**.

![Order with the payment pending](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_payment/order_payment_pending.png)

**Step 2 — Open "Confirm Payment"**

On the order form, click the **⚙** icon next to the order number (actions menu) →
**Confirm Payment**.

![Order actions menu with Confirm Payment](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_payment/order_action_menu.png)

**Step 3 — Fill in and confirm the payment**

The **Confirm Payment** window opens. When the order has a **pending** transaction (our case), the
window picks it up: **Transaction**, **Provider**, **Payment Method** and **Amount** are prefilled
from it. Otherwise **Amount** proposes the **remaining amount** (order total minus **Payment**) and
you choose the provider.

The window never changes an already **confirmed** transaction: on a partially paid order it adds a
new transaction for the remainder, and on a fully paid one it proposes 0 and does nothing. An order
with an **authorized** card payment is refused: capture or cancel the authorization from the payment
provider.

Check before confirming:

- **Amount** is the sum actually received (on the bank statement or in cash), not necessarily the
  order total. A smaller amount leaves the order **Partially paid**;
- **Provider** is the one through which the money came;
- **Payment Date** is the date from the statement (default: today).

Buttons:

- **Confirm** — the transaction becomes confirmed; the order goes to **Paid** (or **Partially paid**);
- **Add** — records the transaction as **pending**, without confirmation (e.g. the customer announced
  the payment, but the money has not arrived yet);
- **Cancel** — closes the window without changes.

The payment date is kept in the order chatter note, in the transaction status message and, for
**electronic** providers, as the date of the accounting payment created by Odoo.

![Confirm Payment window](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_payment/confirm_payment_wizard.png)

**Step 4 — See the paid order**

After **Confirm**, the same order shows **Payment 1,210.00**, the provider **Bank Transfer** and
**Payment Status: Paid** (green).

The transaction is processed immediately, as with electronic providers:

- the quotation is **confirmed automatically** when the payment reaches the prepayment percentage
  required on the quotation (**Online Payment**) or, if the quotation does not require online
  payment, on any payment, even partial. In both cases only if online signature is not required. If
  the quotation requires a signature, it stays a **Quotation** and you confirm it with **Confirm**
  from the order header;
- with automatic invoicing enabled (see *Configuration*), the confirmed order is invoiced: a final
  invoice on full payment, a down payment invoice on partial payment;
- for **Bank Transfer** no accounting payment is created. The accountant registers the payment on the
  invoice or when reconciling the bank statement.

![Order paid in full](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_payment/order_payment_done.png)

**Step 5 — Follow the payments in the order list**

Go to **Sales → Orders → Orders**.

- **Find** — the **Payment Status** column shows the status of each order. Use **Filters** (Without
  payment, Payment initiated, Payment pending, Payment authorized, Partially paid, Paid, Payment
  cancelled) or **Group By → Payment Status** for an overview by group. The **Payment Provider**
  column can be added from the optional columns selector.
- **Check** — **Partially paid** orders have a remainder to collect (order total minus **Payment**).
  Orders **Pending** for several days are announced transfers that have not arrived: follow them up
  with the customer. No prepaid order should ship before it is **Paid**.
- **Go further** — open the order to follow up, or export the list (**select rows → ⚙ Actions →
  Export**) for accounting.

![Order list grouped by payment status](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_payment/order_list_grouped_status.png)
