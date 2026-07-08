1.  Open a **Product Template** whose Unit of Measure needs correcting.
2.  From the gear/Action menu on the product form, run the **Change Uom** action.
3.  In the wizard, pick the new **Unit of Measure** and **Purchase Unit of Measure** (picking one updates the other by default when they are compatible).
4.  Click **Apply**.

The wizard directly updates the product's UoM and rewrites every existing purchase order line, sale order line, invoice/bill line, stock move and stock move line that used the old UoM, so historical documents keep using the corrected unit instead of becoming inconsistent.
