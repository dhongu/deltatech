1. Open the sales order (**Sales > Orders > Quotations** or **Orders**) and click the
   **Order lines** smart button. It opens the **Order Lines** list of this order only.

   ![Quotation form with the product [SC-01] Scaun birou on two lines, described Scaun birou - negru and Scaun birou - gri, and the Order lines button highlighted](static/description/en/01_comanda_buton_linii.png)

   ![Order Lines list of the quotation with the columns Order Reference, Product, Description, Quantity and Unit Price](static/description/en/02_lista_linii.png)

2. To send the lines to the customer, select all the lines and click **Actions > Export**.
   Tick **I want to update data (import-compatible export)**, add the **External ID** field
   (**Description** is already listed), remove the two **Analytic lines/...** fields and click
   **Export**. In this mode the file headers are the technical field names (`id`,
   `product_id`, `name`, `product_uom_qty`...): the customer changes only the values. The `id`
   column links each row to its line, even when the product is on several lines.

   ![Export Data dialog in import-compatible mode, with Description and External ID among the fields to export and no analytic fields](static/description/en/03_export_linii.png)

3. To load the customer's file, open the gear menu next to the **Order Lines** title, choose
   **Import records** and upload the file. Check that each file column is matched with the
   right Odoo field (Product, Quantity, Description...), then click **Test**.

   ![Import a File screen with the Product and Quantity columns of the customer file matched to the Product and Quantity fields](static/description/en/04_import_fisier.png)

4. **Test** changes nothing. If a product is on several lines of the order and the file has
   neither the External ID nor a Description that picks the line, the test stops with an
   error next to the Product column. Import the file exported with the External ID, or add
   the Description column, and test again.

   ![Import test error: the product is on 2 lines of the order, so the row cannot be matched to a single line](static/description/en/05_import_eroare_linii_multiple.png)

5. Click **Import**. Each row updates its line, and the order totals are recomputed.

   ![Quotation after the import: the two chair lines have the quantities 10 and 4 and the table line 3](static/description/en/06_comanda_actualizata.png)

How the rows are matched when the order already has lines:

- a row with an **External ID** (or database **ID**) updates exactly that line; two rows with
  the same ID, or an ID that is not a line of this order (deleted line, file of another
  order), are an error;
- otherwise the row updates the line with the same product, among the lines not taken by
  another row; when the product is on several of them, the **Description** column picks the
  line;
- a row that still matches several lines, or a product with more rows than order lines, is
  reported as an error and the order is not changed;
- a row with a product that is not on the order is skipped.

When the order has no lines yet, every row of the file becomes a new line of the order.
