1. Open *Sales > Reporting > Location Stock*. The **Reporting** menu of Sales is shown to sales
   administrators; the Sales menu is available once the Sales application (`sale_management`) is
   installed.

   ![The Sales app with the Reporting menu open and the Location Stock entry (1) added by the module](static/description/en/01_meniu_locatie_stoc.png)

2. In the **Location Stock** window choose the **Source Location** and the **Partner**: the
   **Reseller Price List** is filled in from the partner's pricelist (you can also pick it directly;
   left empty, the reseller price equals the list price). Tick **Show text instead of stock** to replace
   the quantities with stock level labels: up to the **1st threshold** the report shows the **1st
   threshold text**, up to the **2nd threshold** the **2nd threshold text**, above it the **Above 2nd
   threshold text**. Keep **Refresh Report** ticked to recompute from the current stock, then press
   **Apply**.

   ![The Location Stock window: Source Location (1), Partner (2), Reseller Price List (3), Show text instead of stock (4) with the two thresholds and their texts, Refresh Report (5) and the Apply button (6)](static/description/en/02_fereastra_raport_stoc.png)

3. The **Location Stock Quant Report** lists every product with free quantity in the location (reserved
   quantities excluded), with its **Quantity**, the stock level text (**Qty Text**), the **Reseller
   price** and the **List Price**. Check the labels and prices, then select the lines and use
   **Actions > Export**; leave the **Quantity** column out when the partner should only see the stock
   level texts. The **Description** column shows the internal product description with its HTML tags,
   so leave it out of the export as well.

   ![The report lines; on the first one, USB-C docking station, Quantity 4.00 (1), Qty Text Low stock (2), Reseller price 594.15 lei (3) and List Price 699.00 lei (4)](static/description/en/03_raport_stoc_revanzator.png)

4. Group the lines by **Category of Product** (or **Product**) from the search options, or switch to the
   pivot view. On the group rows, the price columns add up unit prices and are not meaningful.

   ![The same report grouped by Category of Product (1): the first category unfolded with its products and its total quantity](static/description/en/04_raport_grupat_categorie.png)
