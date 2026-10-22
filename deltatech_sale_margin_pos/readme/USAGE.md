Install the module on demand: it is not installed automatically, because it changes the figures of the profit report.

**Step 1 — Sell at the Point of Sale**

Sell and take the payment as usual. In **Point of Sale → Orders → Orders**, the order is *Paid* (or *Posted* after the session is closed), without an invoice. Nothing else is needed: its lines go to the profit report on their own.

![Paid Point of Sale order without invoice](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_margin_pos/01_bon_pos_nefacturat.png)

**Step 2 — See the POS sales in the profit report**

Go to **Sales → Reporting → Profit Analysis** and group the pivot by **Journal**, then by **Product**. The invoices are under the sales journal, the uninvoiced POS orders under the journal of the point of sale, with sale value (without VAT), cost and profit. An invoiced POS order appears only once, through its invoice. A return has negative quantity and values.

While the session is open, the cost is the current product cost; once the session is closed, it is the cost computed by the Point of Sale from the delivery.

![Profit report grouped by journal: invoices and POS](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_margin_pos/02_raport_profit_pe_jurnal.png)

**Step 3 — Only the POS sales**

In the list view, remove the default groupings and the date filter, and choose the **POS Sales** filter (**Invoices** shows only the invoice lines). The **POS Order** column shows the order of each row; group by **POS Order** to sum the lines per order. The POS rows are read-only.

With `deltatech_sale_commission`, the POS rows also get the computed commission of the salesperson of the order, from the rates set on the **invoice journal** of the point of sale.

![POS sales in the profit report](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_margin_pos/03_vanzari_pos_in_raport.png)
