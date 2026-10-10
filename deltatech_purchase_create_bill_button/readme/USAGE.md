Before you start, see the *Configuration* section: the module needs no setup, only a confirmed purchase order.

**Step 1 — Confirm the purchase order**

Go to **Purchase → Orders → Purchase Orders** and open an order. Fill in the **Vendor Reference** (for example the vendor's invoice or delivery note number), then click **Confirm Order**.

![Confirmed purchase order with the Vendor Reference filled in](https://apps.odoocdn.com/apps/assets/19.0/deltatech_purchase_create_bill_button/bill_button_confirmed_order.png)

**Step 2 — Click "Create Bill"**

Once the order is confirmed, a highlighted **Create Bill** button appears in the order's top bar, next to the vendor bill upload widget. It is visible only while the order is in the *Purchase Order* state and still has something to invoice.

![The highlighted Create Bill button next to the upload widget](https://apps.odoocdn.com/apps/assets/19.0/deltatech_purchase_create_bill_button/bill_button_create_bill.png)

Click it. The vendor bill is created straight away, with no attached file required, just like in Odoo 18. The upload widget stays available if you prefer to start from a scanned bill.

**Step 3 — Check the generated bill**

Open the new bill from the order's **Bills** smart button, or from **Accounting → Vendors → Bills**. The **Bill Reference** and **Payment Reference** fields are already filled in with the **Vendor Reference** from the purchase order. If the order has no vendor reference, both fields stay empty.

![Generated bill with Reference and Payment Reference taken from the order](https://apps.odoocdn.com/apps/assets/19.0/deltatech_purchase_create_bill_button/bill_button_generated_bill.png)

As with any bill generated from purchases, review the amounts, taxes and accounts on the lines before confirming it.
