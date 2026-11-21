**Configure the operation type**

1. Go to **Inventory → Configuration → Operation Types** and open the operation type (for example
   **Delivery Orders**). Check **Create Invoice Automatically**, choose the **Invoice Moment** and, for
   customer invoices, **Post Invoice Automatically**.

   ![Delivery Orders operation type with Create Invoice Automatically, Invoice Moment On validation and Post Invoice Automatically](static/description/en/01_tip_operatie_facturare_automata.png)

**Invoice on validation**

2. Validate a delivery of a sale order. The invoice is created right away, with the delivered
   quantities. The transfer shows **Automatic Invoicing** = **Invoiced**, and the **Additional Info**
   tab links the invoice. A return uses the return operation type (for deliveries, usually
   **Receipts**), so the moment and the posting of the credit note are the ones set there.

   ![Validated delivery of order S00101 with Automatic Invoicing Invoiced and the linked invoice](static/description/en/02_livrare_facturata_la_validare.png)

3. With **Post Invoice Automatically**, the customer invoice is posted.

   ![Posted customer invoice with the delivered quantity, 6 Scaun ergonomic Nova](static/description/en/03_factura_client_postata.png)

**Scheduled invoicing**

4. On an operation type with **Invoice Moment** = **Scheduled**, the validated transfers wait as **To
   Invoice** and are invoiced by the daily scheduled action *Generate Invoices from Pickings*. A
   receipt gets a vendor bill in draft, with the received quantities.

   ![Draft vendor bill created for the receipt of order P00101, 5 Birou reglabil Flex](static/description/en/04_factura_furnizor_ciorna.png)

**When the invoicing fails**

5. The transfer stays done and is marked **Failed**. The reason is shown at the top of the form.
   Fix the cause, then click **Retry Invoicing**. Here the receipt was billed by hand from the purchase
   order before the scheduled action, so there is nothing left to bill: in the **Additional Info** tab,
   select the existing bill in **Invoice**, clear **To invoice**, then click **Retry Invoicing**.

   ![Receipt with Automatic Invoicing Failed, the reason The selected receipts are already billed and the Retry Invoicing button](static/description/en/05_receptie_facturare_esuata.png)

6. In **Inventory → Operations → Transfers → Receipts** (or **Deliveries**), add the **Automatic
   Invoicing Failed** filter. Remove the **Receipts** filter to see the failed transfers of all types.
   The **Automatic Invoicing** column can be shown from the optional columns menu.

   ![Receipts list with the Receipts and Automatic Invoicing Failed filters and the Automatic Invoicing column](static/description/en/06_lista_facturare_esuata.png)
