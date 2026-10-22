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

**Step 5 — Check the cost on the customer invoice**

On the customer invoice, the **Cost Price** column shows the unit cost of the goods next to the **Price**. It is computed automatically:
- from the **delivery** of the invoiced order (value of the stock move to the customer divided by quantity, in the unit of the line);
- for kit products, from the delivered components;
- for invoices without an order or delivery, from the product cost;
- for credit notes, from the **goods return**. Without a return, a reversal of the invoice takes the cost of the invoice line (invoice and reversal net to zero profit), while a price or discount reduction has cost 0.

The column is visible only to users in the cost group. On the **Block the sale** policy, a draft invoice with a price below cost cannot be saved.

![Customer invoice with the cost price on each line](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_margin/sale_margin_invoice_cost_price.png)

**Step 6 — Analyse the profit**

Go to **Sales → Reporting → Profit Analysis**. The pivot opens on last month, grouped by product. Each row shows the sale value (without VAT), cost value, profit value, **Markup** (profit / cost) and **Margin** (profit / sale). Regroup by salesperson, category, customer, invoice, journal or month. Totals recalculate markup and margin from the sums. Export the table to Excel with the download button. Credit notes reduce both sale and cost.

The report is shown to the cost group and to the Sales administrators.

![Profit analysis report](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_margin/sale_margin_profit_report.png)

**Step 7 — Recompute the cost when needed**

If a line cost is wrong (for example the delivery was validated after invoicing), switch the report to the **list** view, remove the *Product* grouping from the search, select the lines and choose **Actions → Update Purchase Price**:
- **Price from delivery** (default) recomputes the cost from the delivery, falling back to the product cost;
- unchecked, it takes the current product cost, without unit conversion: keep the default;
- **For all lines** applies to every line in the report, from all periods: it rewrites the profit of periods already reported.

A scheduled action also refreshes, every day, the cost of the lines invoiced in the last 7 days. Only the Sales administrators (and, with `deltatech_sale_commission`, the Commission Managers) can run the wizard.

![Update Purchase Price wizard](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_margin/sale_margin_update_cost_wizard.png)
