Open **Inventory > Operations > Simple Production** and click **New**.

1. Choose the *Picking type consume* and the *Picking type receipt*. Tick
   *Validation Consume* and/or *Validation Receipt* to have each transfer validated
   automatically (the receipt is ticked by default).

   ![Simple Production form in Draft with the two picking types and the validation options](static/description/en/01_document_nou.png)

2. In **Consume**, add the components with their quantity and unit of measure (**Add
   lines** adds several at once). The value of a line is the quantity, converted to the
   product unit, times the cost: 2 dozens at 1.20 per unit are worth 28.80.

   ![Consume list with 2 dozens of a component valued at 28.80](static/description/en/02_linii_consum.png)

3. In **Receipt**, add the products obtained and click **Recompute prices**: the consumed
   cost is split over them, and the unit price can still be changed by hand.

   ![Receipt list with the cost allocated to the product obtained and the Recompute prices button highlighted](static/description/en/03_linii_receptie.png)

4. Click **Confirm**. The consumption and receipt transfers are created and validated, and
   open from the **Consume** and **Receipt** smart buttons.

   ![Confirmed document with the Consume and Receipt buttons highlighted](static/description/en/04_confirmat.png)

   If the consumption cannot be completed in full and the picking type asks for the backorder
   decision, Odoo shows its dialog and the document stays in Draft. Choose, then click
   **Confirm** again to continue with the receipt.

   ![Create Backorder dialog shown over the document](static/description/en/05_dialog_backorder.png)

5. With **Create product & sale** ticked, **Confirm** also creates the final product and a
   quotation for the client, which has the **MRP Simple** smart button.

   ![Quotation with the MRP Simple smart button highlighted](static/description/en/06_oferta_mrp_simple.png)
