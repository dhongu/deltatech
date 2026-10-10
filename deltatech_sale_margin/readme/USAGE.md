Before you start, set the policy and the margin limit as described in *Configuration*.

**Step 1 — Create the order**

Go to **Sales → Orders** and create a quotation. Add a product that has a purchase cost, and enter the **Unit Price**.

**Step 2 — See the signal**

As soon as you leave the price field, if the margin falls below the configured limit, the line is highlighted and a banner appears at the top of the order. The signal comes when the price is decided, not at confirmation, when it is too late.

On the **Warn only** policy the banner states that the order can be confirmed, so nobody waits for an approval that does not exist. On the **Block the sale** policy, a user outside the exception group gets an error and cannot save the price.

The comparison is made in the unit of the line. Example: at a cost of 3 per kg, a 12 kg box costs 36, so a price of 30 per box is below cost.

| What you see | What it means |
|---|---|
| Highlighted line and banner | The margin is below the configured limit |
| **Margin** at the bottom of the order | The exact figure, shown only to users allowed to see costs |
| **Confirm** button active | The order is not blocked (Warn only policy) |
| Nothing, although the price looks low | The product has no cost, or the units cannot be compared (for example a wrong base unit) |

![Order below cost: banner, highlighted line and negative margin, with the Confirm button active](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_margin/sale_margin_below_cost_order.png)

**Step 3 — Confirm the order**

Click **Confirm**. On the **Warn only** policy, the order chatter receives one note listing the lines sold below cost and the margin of each. The note is written once, at confirmation, not on every price correction.

**Step 4 — Invoice**

The same policy applies on the customer invoice line, so an invoice for an order sold below cost is created without error on **Warn only**.

Delivery lines, services, loyalty rewards and website orders are not checked.
