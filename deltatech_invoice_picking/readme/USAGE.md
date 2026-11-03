**Invoice a delivery**

1. Go to **Inventory → Operations → Transfers → Deliveries** and apply the **To invoice** filter. The list shows the
   done deliveries that are not invoiced yet, or only partly invoiced. To invoice several deliveries at
   once, select them and use **Actions → Create Sale Invoices**.

   ![Deliveries list with the To invoice filter: the done deliveries of orders S00101, S00102 and S00103](static/description/en/01_livrari_de_facturat.png)

2. Open a done delivery that comes from a sale order. The **Invoice** button is shown while the delivery
   is to invoice.

   ![Done delivery of order S00101 with the Invoice button and the delivered quantities, 6 chairs and 2 desks](static/description/en/02_livrare_buton_factura.png)

3. Click **Invoice**. The standard **Create invoice(s)** wizard opens: keep **Regular invoice** and
   click **Create Draft**.

   ![Create invoice(s) wizard opened from the delivery, with Regular invoice selected and the Create Draft button](static/description/en/03_asistent_facturare.png)

4. The invoice contains only the products of the selected deliveries, with the delivered quantities
   (6 chairs out of the 10 ordered). Its product lines cannot be changed or deleted, so the invoice
   stays equal to the delivery.

   ![Customer invoice created from the delivery: 6 Scaun ergonomic Nova and 2 Birou reglabil Flex, with 21% VAT](static/description/en/04_factura_din_livrare.png)

5. On the delivery, the **Additional Info** tab shows the invoice, and **To invoice** is cleared. If the
   invoice is cancelled or deleted, the delivery is to invoice again.

   ![Invoiced delivery: the Additional Info tab shows the invoice and To invoice is cleared](static/description/en/05_livrare_facturata.png)

6. A delivery that is only partly invoiced is linked to the invoice but stays **To invoice**, so the rest
   can be invoiced. The flag follows all the done moves of the transfer and the quantity invoiced on each
   order line (invoices minus refunds, cancelled ones excluded).

   ![Partly invoiced delivery of order S00102: the invoice is linked, To invoice is still set and the Invoice button is still shown](static/description/en/06_livrare_facturata_partial.png)

**Bill a receipt**

1. In **Inventory → Operations → Transfers → Receipts**, open a done receipt that comes from a purchase
   order, fill in **Supplier Invoice No** and click **Bill**. Several receipts can be
   billed from the list with **Actions → Create Purchase Invoices**.

   ![Done receipt of order P00101 with Supplier Invoice No BM-2026-0457 and the Bill button](static/description/en/07_receptie_numar_factura.png)

2. A draft vendor bill is created with the received quantities. The supplier invoice number is copied
   to the purchase order as **Vendor Reference** and shown on the **Purchases** button of the bill; fill
   in **Bill Reference** and **Bill Date** before **Confirm**. A receipt that is already fully billed
   cannot be billed again.

   ![Draft vendor bill created from the receipt: the Purchases button shows P00101 (BM-2026-0457) and the line has 5 Birou reglabil Flex](static/description/en/08_factura_furnizor.png)

**Invoice a batch**

Open a done batch in **Inventory → Operations → Jobs → Batch Transfers** and click **Invoice**. The
transfers of the batch that are not invoiced, or only partly invoiced, go on the invoice; the fully
invoiced ones are skipped. For a batch of receipts, fill in **Supplier Invoice No** on each receipt first.
Batches need **Inventory → Configuration → Settings → Batch, Wave & Cluster Transfers**.

![Done batch BATCH/00101 with the Invoice button](static/description/en/09_lot_buton_factura.png)

**Refund a return**

A validated return of an invoiced delivery is **To invoice**, with no invoice linked. Click **Invoice**
on the return and **Create Draft**: Odoo creates the customer credit note with the returned quantity
and links it to the return. A credit note made from the invoice with **Credit Note** does not update the
return.

![Return of delivery DC/OUT/00001, done: no invoice, To invoice set and the Invoice button](static/description/en/11_retur_de_facturat.png)

![Credit note created from the return: 2 Scaun ergonomic Nova, 1,089.00 lei](static/description/en/12_nota_credit_retur.png)

**Invoice the ordered quantities**

On the sale order, the **Other Info** tab has **Force Invoice Order**: the order lines are invoiced on the
ordered quantities, whatever the invoicing policy of the product. When the invoice starts from a
transfer, the quantities are still those of the transfer.

![Sale order S00101, Other Info tab, with the Force Invoice Order field](static/description/en/10_comanda_facturare_fortata.png)
