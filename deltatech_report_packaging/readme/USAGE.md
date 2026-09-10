Set the packaging materials on the product, in the **Packaging materials** section of
the product form. Each material takes two quantities per unit: **Purchase quantity**,
for the way the vendor packs the product, and **Sale quantity**, for the way it is
packed when shipped to the customer. Leave one of them at zero for a material used in
a single direction.

On a customer or vendor invoice, the **Packaging materials** tab shows the quantity of
each material, computed as the invoiced quantity multiplied by the quantity configured
on the product — the purchase quantity on vendor bills and refunds, the sale quantity
on customer invoices and credit notes. Materials with a zero quantity in that direction
are not reported. The quantities are computed again when the invoice is posted.

To correct a quantity, edit it — or delete the line — directly in the tab. The
**Auto-update packaging materials** switch in the tab is unset automatically, and the
validation of the invoice no longer overwrites what you entered. Press **Refresh** to
discard the corrections, compute the quantities from the invoice lines again and put
the invoice back under automatic update.

To obtain the aggregate report, select several invoices in the list view and run the
packaging-material report action.
