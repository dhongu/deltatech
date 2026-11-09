1. Go to *Inventory > Configuration > Settings*, section *Traceability*, and enable
   **No negative stock**. The setting applies to the current company; in a
   multi-company database, enable it on each company.

2. Right below it, decide on **Allow negative stock from Point of Sale** (enabled by
   default). Point of Sale validates the delivery of a receipt in the background and does
   not show the cashier an error, so a refused delivery would only leave the stock
   undeducted:
   - enabled: a receipt's delivery is validated even when it takes the location below
     zero; the bypass is logged and the location shows negative stock to correct;
   - disabled: the rule applies to receipts as well, and their deliveries stay
     unvalidated until the stock is there.

   A Point of Sale delivery is recognised by the operation type set on the Point of Sale
   (by default the warehouse's *PoS Orders*): a transfer created by hand with that same
   operation type is treated as a register delivery too, so keep that type for Point of
   Sale only. The setting has no effect when Point of Sale is not installed.

![No negative stock and Allow negative stock from Point of Sale in Settings](static/description/en/01_setari_fara_stoc_negativ.png)

3. Enable *Storage Locations* (section *Warehouse*) to see the location options. Open
   *Inventory > Configuration > Locations* and, on the internal locations where stock may
   go below zero (transit, work in progress), check **Allow Negative Stock**.

4. For products tracked by serial number, **Check Serial No.** (enabled by default)
   checks the serial number of the line. Uncheck it on a location to check the total of
   all serial numbers there; reservation then also ignores the serial number.

![Location form with Allow Negative Stock and Check Serial No.](static/description/en/02_locatie_optiuni.png)

5. Before enabling the rule on an existing database, review the negative positions
   (*Inventory > Reporting > Stock by Location*, filter *Negative Stock*): record the missing
   receipts or transfers first, and use an inventory adjustment only for the real
   differences. Negative positions left in place block every outgoing move from them.
