1. **Define the consumption purposes** in *Inventory → Configuration → Consumption purposes*
   (e.g. *Own use*, *Investments*). The list is empty after installation; archive a purpose that
   is no longer used instead of deleting it.

   ![Consumption purposes list with the Name and Company columns](static/description/en/01_destinatii_consum.png)

2. **Pick the purpose on the consumption voucher.** On a transfer to a consumption location the
   *Consumption purpose* field appears under *Source Document*; it is required until the transfer
   is validated and can still be filled in on validated vouchers. A return keeps the purpose of the
   original voucher.

   ![Validated consumption voucher with the operation type and the consumption purpose highlighted](static/description/en/02_bon_consum.png)

3. **The journal entry of the voucher** is posted at validation. The report takes the value of each
   consumption from it (the credit of the product lines); a voucher without an entry
   is valued at the stock value of the move.

   ![Journal entry of the consumption voucher: expense account debited, stock accounts credited](static/description/en/03_nota_consum.png)

4. **Goods used internally** are not issued for consumption straight from the sale stock (that
   books them on the cost of goods sold). Move them first with an internal transfer to a materials
   location of the store (with its own stock and expense accounts; with the Romanian localisation
   the entry is Dr 3028 = Cr 371 at cost), then issue the consumption voucher from that location.

   ![Journal entry of the internal transfer of goods to the materials location](static/description/en/04_transfer_marfa.png)

5. **Open the report** from *Inventory → Reporting → Consumption report*. The period defaults to
   the current month and the operation types whose default destination is a consumption location
   are preselected; empty the field to include every consumption of the period.

   ![Consumption report wizard with the period, the operation types and the Export XLSX and View buttons](static/description/en/05_wizard_raport.png)

6. **Check the figures on screen** with *View*: a pivot by store, purpose and product, with
   quantity and value. Rows marked *Undefined* are vouchers without a purpose.

   ![Consumption pivot by store, purpose and product](static/description/en/06_pivot_consumuri.png)

7. **Export XLSX** for the accountant. The *Summary* sheet has one row per store and purpose; its
   total equals the total of the pivot.

   ![Summary sheet of the XLSX export, by store and purpose](static/description/en/07_xlsx_centralizat.png)

8. The *Detail* sheet has one row per store, purpose and product, with category, average cost,
   *Can be sold* and the quantity delivered to customers in the last 6 months, to spot goods meant
   for sale that were issued for consumption straight from the sale stock.

   ![Detail sheet of the XLSX export, by store, purpose and product](static/description/en/08_xlsx_detaliat.png)
