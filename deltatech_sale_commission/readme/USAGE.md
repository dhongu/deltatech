1. Go to **Sales > Configuration > Settings** and choose how the salesperson for the commission is determined: from the **Invoice** or from the **Sale Order** (field "Salesperson commission compute").
2. Go to **Sales > Configuration > Users Commission** to set, per user, the commission **rate**, and optionally a **manager**/**director** with their own rates and the sales **journal** the rule applies to.
3. Optionally set the system parameter `deltatech_sale_commission.days_for_commission` (Settings > Technical > Parameters > System Parameters) to an integer number of days. When set, a commission is only granted if the invoice was fully paid within that many days after its due date; otherwise the commission is forced to 0.
4. Use the technical access groups to control visibility/behaviour on customer invoices:
   - **Show purchase price on sale order lines and customer invoice** – lets a user see margin/purchase price.
   - **No change price on sale order** – prevents a user from changing the price.
   - **Sell below the purchase price** – allows selling below cost without a blocking warning.
5. Open the **Sale Margin Report** (available from the profitability report/list) to review invoice lines with their sale value, cost, and profit.
6. From that list, select one or more lines and use:
   - **Compute Commission** (list action) to calculate the commission for the selected lines, respecting the paid/days rule above.
   - **Update Purchase Price** (list action) to (re)fill the purchase price from the delivery/source document or from the product's cost, either for the selected lines or for all lines ("For all lines" option).
   - **Set Paid** (list header button) to mark commissions as paid once settled.
7. A daily cron job **Update Purchase Price Daily** runs automatically (active by default) and refreshes purchase prices on the margin report; no manual action is required.
