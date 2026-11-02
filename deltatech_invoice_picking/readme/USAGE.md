**Invoice a delivery**

1. Validate the delivery in **Inventory > Operations > Transfers > Deliveries**. A delivery that comes from a
   sale order gets the **To invoice** flag (tab **Additional Info**) and an **Invoice** button.

   ![Done delivery with the Invoice button and the To invoice flag checked](static/description/en/01_livrare_de_facturat.png)

2. Click **Invoice**. The standard invoicing window of the sale order opens; keep **Regular invoice**
   and click **Create Draft**.

   ![Create invoice(s) window opened from the delivery, with Create Draft highlighted](static/description/en/02_fereastra_creare_factura.png)

3. The draft invoice holds only the quantities delivered in the selected transfers (6.00), not the
   whole order (10). In the **Other Info** tab, **Created from pickings** is checked. On such an invoice, the
   quantity and the product of storable lines cannot be changed and these lines cannot be deleted.

   ![Draft customer invoice, Invoice Lines tab: one line with quantity 6.00 at 45.00, total 326.70 lei](static/description/en/03_factura_din_livrare.png)

4. Back on the delivery, **To invoice** is cleared and the invoice is linked. If the invoice is
   cancelled or deleted, the delivery is flagged **To invoice** again.

   ![Invoiced delivery: the invoice is linked and To invoice is cleared](static/description/en/04_livrare_facturata.png)

**Invoice several deliveries**

5. In **Inventory > Operations > Transfers > Deliveries**, use the **To invoice** filter, select the done deliveries and choose
   **Actions > Create Sale Invoices**. Backorders still to deliver keep the flag of their origin
   delivery but cannot be invoiced until they are done.

   ![Deliveries filtered To invoice, one done delivery selected and the Actions menu open](static/description/en/05_livrari_de_facturat.png)

**Bill a receipt**

6. On a done receipt from a purchase order, fill in **Supplier Invoice No** and click **Bill**.

   ![Done receipt with Supplier Invoice No filled in and the Bill button](static/description/en/06_receptie_nr_factura.png)

7. The vendor bill holds the received quantities. The supplier invoice number is saved as the vendor
   reference of the purchase order; on Odoo 19 the **Bill Reference** of the bill is not filled in
   automatically, so copy it before confirming the bill.

   ![Draft vendor bill created from the receipt, with the Bill Reference field to fill in](static/description/en/07_factura_furnizor.png)

**Invoice a batch**

8. A done batch of deliveries has an **Invoice** button that invoices its transfers not invoiced yet; a
   batch of receipts creates the vendor bill. Delivery and receipt batches cannot be invoiced together.

   ![Done batch transfer with two deliveries and the Invoice button](static/description/en/08_lot_facturare.png)
