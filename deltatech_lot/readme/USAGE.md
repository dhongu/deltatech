1. Track the product by lots: open the product (*Inventory > Products > Products*), tab **General
   Information**, tick **Track Inventory** and choose **By Lots**.

   ![Product form, General Information tab: Track Inventory ticked with By Lots (1)](static/description/en/01_produs_urmarire_loturi.png)

2. Open the receipt from the vendor (*Inventory > Operations > Transfers > Receipts*), in the **Ready**
   state. The receipt operation type must have **Create New** ticked in its **Lots/Serial Numbers** group
   (the default for receipts).

   ![Receipt from Vopsele Demo SRL in the Ready state, with the Validate button (1)](static/description/en/02_receptie_de_validat.png)

3. In **Details**, the **Lot/Serial Number** column can stay empty; split the quantity over the storage
   locations in **Store To** if needed. Type the vendor's lot number only on the lines where it must be
   kept. Save and press **Validate**.

   ![Detailed Operations: two lines, 12 to WH/Stock/Raft A1 and 8 to WH/Stock/Raft B2, with an empty Lot/Serial Number column (1)](static/description/en/03_operatii_detaliate_fara_lot.png)

4. The receipt is done and every line without a lot got its own lot number from the **Serial Numbers**
   sequence.

   ![The done receipt: lot 0000001 on Raft A1 and lot 0000002 on Raft B2 (1)](static/description/en/04_loturi_generate_receptie.png)

5. In *Inventory > Products > Lots / Serial Numbers*, remove the default **Location** grouping: the
   **Location** column shows where each lot is. A lot spread over several locations has no location.

   ![List of lots: 0000001 on WH/Stock/Raft A1, 0000002 on WH/Stock/Raft B2 and VOP-2509-07, spread over two shelves, with an empty Location (1)](static/description/en/05_lista_loturi_locatie.png)

6. The lot form shows the same **Location**. Changing it moves the stock of the lot when it is all in
   one location.

   ![Lot 0000001 with Location WH/Stock/Raft A1 (1)](static/description/en/06_fisa_lot_locatie.png)

7. Search the lots by location: type the location and choose **Search Location for**. Only the lots
   held entirely in that location are listed.

   ![The list of lots filtered by Location: Raft A1 (1), showing only lot 0000001](static/description/en/07_cautare_loturi_locatie.png)

Lot numbers are generated only on receipts and dropships, only for products tracked by lots (not by
serial numbers), and always from the general **Serial Numbers** sequence, not from the custom prefix
set on the product.
