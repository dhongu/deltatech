1. Go to **Invoicing → Configuration → Settings**. In the **Customer Invoices** section, check
   **Customer invoices for storable products only from sale orders** and click **Save**. The option is
   saved on the current company.

   ![Invoicing settings, Customer Invoices section: the option Customer invoices for storable products only from sale orders is checked and highlighted](static/description/en/01_setare_facturi_clienti.png)

2. If all purchases of goods go through purchase orders, check also **Vendor bills for storable
   products only from purchase orders**, in the **Vendor Bills** section.

   ![Invoicing settings, Vendor Bills section: the option Vendor bills for storable products only from purchase orders is checked and highlighted](static/description/en/02_setare_facturi_furnizori.png)

3. A customer invoice or credit note with a storable product that does not come from a sale order can
   no longer be confirmed: **Confirm** shows the products without a sale order. Create the sale order,
   deliver the goods and invoice from the order. Sales receipts and the confirmation from the list
   (**Actions → Confirm Entries**) are checked too. A credit note created from an invoice issued from an
   order keeps the link and is confirmed normally. Lines with services are not checked. To invoice
   only what was delivered, set the product **Invoicing Policy** to **Delivered quantities**.

   ![Draft customer invoice for Client Demo SRL with the storable product Marfă depozit, and the Invalid Operation dialog: storable products can be invoiced only from a sale order](static/description/en/03_factura_client_fara_comanda.png)

4. In the same way, a vendor bill or refund with a storable product that does not come from a purchase
   order cannot be confirmed. Fill the bill from the purchase order (**Auto-Complete** field) or create
   the purchase order and the receipt first.

   ![Draft vendor bill from Furnizor Demo SRL with the storable product Marfă depozit, and the Invalid Operation dialog: storable products can be billed only from a purchase order](static/description/en/04_factura_furnizor_fara_comanda.png)
