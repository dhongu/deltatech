1. Go to *Point of Sale > Configuration > Settings* and select the register in the
   *Point of Sale* field at the top. The setting is per register.
2. In the *PoS Interface* section, under *Product Stock*, tick *Show stock* and *Show price*
   (both are ticked by default) and choose the *Quantity shown*:
   - *On hand* (default): the physical stock of the register's warehouse;
   - *Available*: the stock minus everything already reserved for other operations
     (deliveries, internal transfers, manufacturing) that has not left the warehouse yet. Use
     it where the picking is validated by the warehouse, not at the till.

   Save, and reload the register page if a session is already open.

   ![Product Stock block in the Point of Sale settings, with Show stock, Show price and Quantity shown](static/description/en/01_setari_stoc.png)

3. Open the register. Each product card shows a badge with the price (in yellow) and, for
   products that track inventory, the quantity in stock. Products with nothing left show the
   quantity in red. The badge follows stock changes live: receipts, transfers, inventory
   adjustments and, with *Update quantities in stock* set to real time (the default), the sales
   of every register.

   ![Product cards in the register with the price and stock badge, one product out of stock with its quantity highlighted in colour](static/description/en/02_pos_badge_stoc_pret.png)

4. Adding a product with no stock left raises a warning, "*product* is out of stock.". The
   sale is not blocked: the product goes on the order as usual. The warning compares the badge
   with zero; the quantities already on the current order are not subtracted.

   ![Warning shown when a product without stock is added to the order](static/description/en/03_pos_avertizare_fara_stoc.png)

5. On a register set to *Available*, the badge subtracts the reservations: 25 kg on hand with
   5 kg reserved for a delivery shows 20.

   ![Register set to Available: the coffee badge shows 20, the stock on hand minus a 5 kg reservation](static/description/en/04_pos_cantitate_disponibila.png)

The stock shown is the stock of the register's warehouse: the warehouse of its *Operation Type*,
or the *Warehouse* set under *Allow Ship Later*.
