Before you start, see *Configuration* for access groups, agent rates and the optional payment-delay limit.

**Step 1 — Choose who earns the commission**

Go to **Settings → Sales**, section **Invoicing**, option **Salesperson commission compute**. Choose **Invoice** (the agent set on the invoice) or **Sales Order** (the agent of the order the line was invoiced from), then click **Save**. Decide this at implementation time: changing it later reassigns all existing lines, including commissions already paid.

![Setting that decides which agent earns the commission](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_commission/commission_settings_agent.png)

**Step 2 — Set the rates per agent**

Go to **Sales → Configuration → Users Commission**. The list is editable in place. For each agent enter the agent rate, the sales manager and director with their own rates, and the sales journal. Rates are fractions of the profit: 0.100 means 10%. The journal is mandatory, and an agent can have only one row per journal.

![Commission rates per agent, manager and director](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_commission/commission_agent_rates.png)

The cost on the invoice lines, the **Profit Analysis** report and the cost recalculation come from `deltatech_sale_margin`; see its usage guide.

**Step 3 — Review the commissions to compute**

Go to **Sales → Orders → Commission → Commission**. The list opens on last month and only on **paid** invoices (including *In payment*); remove the *Paid* filter to see unpaid ones as well. Each line shows the invoice, product, agent, customer, sale, cost, profit, **Computed commission** (agent rate × profit), **Real commission** (initially 0) and **Commission paid**. Manager and director commissions are optional columns and are informative only. Point of Sale orders of `deltatech_sale_margin_pos` are not in this list: their computed commission shows in **Profit Analysis**.

![Commission list before the calculation](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_commission/commission_list_before.png)

**Step 4 — Compute the commissions**

Select the lines and choose **Actions → Compute Commission**. The wizard lists the selected lines. Click **Apply**. **Real commission** becomes:
- the computed commission, if the `deltatech_sale_commission.days_for_commission` parameter is not set;
- with the parameter: 0 if the invoice is not fully paid or was paid later than that number of days after the due date, otherwise the computed commission;
- for credit notes: always the computed commission, which is negative and reduces the agent's total.

Only the agent's commission is written; manager and director amounts stay informative.

![Compute Commission wizard](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_commission/commission_compute_wizard.png)

**Step 5 — Review the result**

After **Apply**, the list opens on the computed lines. Compare **Computed commission** with **Real commission**: every line with real commission 0 is an unpaid invoice or one paid after the limit, and the difference between the totals is the amount lost to late payment. If needed, correct **Real commission** manually before payment: open the row and edit the field in the form.

![Commissions after the calculation](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_commission/commission_list_after.png)

**Step 6 — Mark commissions as paid**

After the agent has been paid (outside this module), select the lines and click **Set Paid** in the list header. The filters **Commission not paid** and **Commission paid** then separate what is settled from what is still due.

![Commission marked as paid](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_commission/commission_marked_paid.png)
