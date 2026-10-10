Before you start, see *Configuration* for access groups, agent rates and the optional payment-delay limit.

**Step 1 — Choose who earns the commission**

Go to **Settings → Sales**, section **Invoicing**, option **Salesperson commission compute**. Choose **Invoice** (the agent set on the invoice) or **Sales Order** (the agent of the order the line was invoiced from), then click **Save**. Decide this at implementation time: changing it later reassigns all existing lines, including commissions already paid.

![Setting that decides which agent earns the commission](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_commission/commission_settings_agent.png)

**Step 2 — Set the rates per agent**

Go to **Sales → Configuration → Users Commission**. The list is editable in place. For each agent enter the agent rate, the sales manager and director with their own rates, and the sales journal. Rates are fractions of the profit: 0.100 means 10%. The journal is mandatory, and an agent can have only one row per journal.

![Commission rates per agent, manager and director](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_commission/commission_agent_rates.png)

**Step 3 — Check the cost on the customer invoice**

On the customer invoice, the **Cost Price** column shows the unit cost of the goods next to the **Price**. It is computed automatically:
- from the **delivery** of the invoiced order (value of the stock move to the customer divided by quantity);
- for kit products, from the delivered components;
- for invoices without an order or delivery, from the product cost;
- for credit notes, from the **goods return**. Without a return, a reversal of the invoice takes the cost of the invoice line (invoice and reversal net to zero profit), while a price or discount reduction has cost 0.

The column is visible only to users in the cost group from `deltatech_sale_margin`. If your company uses the **Block sale** policy, a draft invoice with a price below cost cannot be saved.

![Customer invoice with the cost price on each line](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_commission/commission_invoice_cost_price.png)

**Step 4 — Analyse the profit**

Go to **Sales → Reporting → Profit Analysis**. The pivot opens on last month, grouped by product. Each row shows the sale value, cost value, profit value, **Markup** (profit / cost) and **Margin** (profit / sale). Regroup by agent, category, customer, invoice, journal or month. Totals recalculate markup and margin from the sums. Use **Insert in Spreadsheet** or the export to take the table to Excel. Credit notes reduce both sale and cost.

![Profit analysis report](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_commission/commission_profit_report.png)

**Step 5 — Review the commissions to compute**

Go to **Sales → Orders → Commission → Commission**. The list opens on last month and only on **paid** invoices (including *In payment*); remove the *Paid* filter to see unpaid ones as well. Each line shows the invoice, product, agent, customer, sale, cost, profit, **Computed commission** (agent rate × profit), **Real commission** (initially 0) and **Commission paid**. Manager and director commissions are optional columns and are informative only.

![Commission list before the calculation](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_commission/commission_list_before.png)

**Step 6 — Compute the commissions**

Select the lines and choose **Actions → Compute Commission**. The wizard lists the selected lines. Click **Apply**. **Real commission** becomes:
- the computed commission, if the `deltatech_sale_commission.days_for_commission` parameter is not set;
- with the parameter: 0 if the invoice is not fully paid or was paid later than that number of days after the due date, otherwise the computed commission;
- for credit notes: always the computed commission, which is negative and reduces the agent's total.

Only the agent's commission is written; manager and director amounts stay informative.

![Compute Commission wizard](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_commission/commission_compute_wizard.png)

**Step 7 — Review the result**

After **Apply**, the list opens on the computed lines. Compare **Computed commission** with **Real commission**: every line with real commission 0 is an unpaid invoice or one paid after the limit, and the difference between the totals is the amount lost to late payment. If needed, correct **Real commission** manually before payment: open the row and edit the field in the form.

![Commissions after the calculation](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_commission/commission_list_after.png)

**Step 8 — Mark commissions as paid**

After the agent has been paid (outside this module), select the lines and click **Set Paid** in the list header. The filters **Commission not paid** and **Commission paid** then separate what is settled from what is still due.

![Commission marked as paid](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_commission/commission_marked_paid.png)

**Step 9 — Recompute the cost when needed**

If a line cost is wrong (for example the delivery was validated after invoicing), select the lines and choose **Actions → Update Purchase Price**:
- **Price from delivery** (default) recomputes the cost from the delivery, falling back to the product cost;
- unchecked, it takes the current product cost;
- **For all lines** applies to every line in the report, not only the selected ones.

Profit and computed commission update immediately; **Real commission** stays as set until you compute again (Step 6). A scheduled action also refreshes the cost of lines invoiced in the last 7 days every day.

![Update Purchase Price wizard](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_commission/commission_update_cost_wizard.png)
