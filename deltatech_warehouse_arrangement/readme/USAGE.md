1. Create the storehouse (*Inventory > Locations > Storehouse*): its **Name** (1) and, in
   **Warehouse** (2), the Odoo stock location where it stands (e.g. `WH/Stock`). Receipts into this
   location fill in the arrangement of the lots. Then create the zones, shelves and sections, each
   linked to the level above.

   ![Storehouse form: Name H1 (1), Warehouse WH/Stock (2) and Full Name Stock/H1 (3)](static/description/en/01_hala_formular.png)

2. Create the racks (*Inventory > Locations > Rack*). The section of each rack shows the full path.

   ![Rack list: P01 and P02 in section S1, with the path Storehouse: H1/Zone: Z1/Shelf: R01/Section: S1](static/description/en/02_lista_polite.png)

   On the rack, choose the **Section** (1); **Full Name** (2) shows the whole path, and **Barcode** (3)
   is the code scanned when moving lots.

   ![Rack P01: Section S1 (1), Full Name (2) and Barcode H1-Z1-R01-S1-P01 (3)](static/description/en/03_polita_formular.png)

3. Print the rack labels: in the list, select the racks, then **Print** > **Rack Labels**; on a rack
   form, the gear ⚙ next to the title > **Rack Labels**.

   ![Rack label: Code128 barcode and the full path of rack P01](static/description/en/04_eticheta_polita.png)

4. On the product (*Inventory > Products > Products*), tab **Locations**, choose the default
   arrangement: **Storehouse**, **Zone Location**, **Shelf Location**, **Section Location** and
   **Rack Location**. Each list only shows the items of the level above.

   ![Product Copper cable 2.5 mm², tab Locations: Storehouse H1 to Rack Location P01 (1-5)](static/description/en/05_produs_locatii.png)

5. Receive the lots into the main location of the storehouse (*Inventory > Operations > Receipts*,
   **Details** on the product line) and validate the receipt.

   ![Done receipt, Detailed Operations: lots LOT-2026-001 and LOT-2026-002 (1) stored in WH/Stock (2)](static/description/en/06_receptie_loturi.png)

6. On the lot (*Inventory > Products > Lots / Serial Numbers*), tab **Locations**, check that the lot
   took the arrangement of the product. It can be changed here by hand at any time.

   ![Lot LOT-2026-001, tab Locations: the arrangement H1 / Z1 / R01 / S1 / P01 (1-5) taken from the product](static/description/en/07_lot_locatii_receptie.png)

7. To move a lot to another rack, open *Inventory > Operations > Adjustments > Change lot* and scan
   the lot label, then the new rack label: **Lot** (1) and **Rack** (2) are filled in.

   ![Change lot screen after scanning: Lot LOT-2026-002 (1) and Rack P02 (2), Lot Scanned checked](static/description/en/08_schimbare_locatie_lot.png)

   In Odoo 19 this screen opens full page and its **Apply** / **Reset** buttons are not shown, so the
   scan does not change the lot. Until this is fixed, choose the new rack directly on the lot, tab
   **Locations**, field **Rack Location**, and save.

   ![Lot LOT-2026-002, tab Locations: Rack Location (1) is now P02](static/description/en/09_lot_polita_noua.png)

8. Find the stock by rack in *Inventory > Reporting > Locations* (shown only with the *Storage
   Locations* option, the consignment option or in developer mode; otherwise use the **On Hand** button
   of the product, which opens the same list): each lot (1) shows its storehouse,
   zone, shelf, section and rack (2). Search or group by **Storehouse**, **Zone**, **Shelf**,
   **Section** or **Rack**.

   ![Locations list for CBL-CU25: LOT-2026-001 on rack P01 and LOT-2026-002 on rack P02, both in WH/Stock](static/description/en/10_stoc_pe_polite.png)

When the whole quantity of a lot leaves the main location of the storehouse, the arrangement of the
lot is cleared (only moves out of the main location itself trigger this, not moves out of its
sublocations). The arrangement is informative only: it does not
change the Odoo stock locations, the quantities or the stock valuation.

Only users of the *Warehouse Locations manager* group can create or change the storehouses, zones,
shelves, sections and racks; the other internal users can read them.
