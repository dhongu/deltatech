Work with transfers as usual. The check runs when a transfer is **validated**, on every
line that takes stock out of an internal location, and on all lines together.

1. **Prepare a transfer.** In this example the location *Raft A* holds 1 unit of the
   product, and the transfer picks it twice, 1 unit per line, in *Detailed Operations*.
   Each line alone would fit; together they need 2 units.

   ![Detailed Operations with two lines of 1 unit picked from Raft A, on a stock of 1 unit](static/description/en/03_transfer_doua_linii.png)

2. **Validate.** The lines are added up per location, lot, package and owner, after
   converting the units of measure. When the location would go below zero, validation
   stops with an *Invalid Operation* message naming the product, the location and the
   quantity that would remain (here -1). Nothing is moved: lower the quantities, pick from
   another location or lot, or validate the missing receipt first.

   ![Invalid Operation dialog: you have chosen to avoid negative stock, with the product, the remaining quantity and the location](static/description/en/04_eroare_stoc_negativ.png)

3. **Check the stock positions.** *Inventory > Reporting > Locations* shows the positions
   the check compares against: one row per product, location, lot or serial number,
   package and owner. The check uses *On Hand*, not *Available*: a line on one lot,
   package or owner cannot use the stock of another.

   ![Stock positions per location, lot, package and owner](static/description/en/05_pozitii_stoc.png)

4. **Locations allowed to go negative.** On a location with **Allow Negative Stock**, the
   same transfer is validated and the position stays negative. Incoming moves are never
   checked, only the source location of a move.

   ![Negative position on WH/Stock/Tranzit, the location that allows negative stock](static/description/en/06_locatie_stoc_negativ_permis.png)

5. **Serial numbers.** With **Check Serial No.** unchecked on the location, the stock is
   checked on the total of all serial numbers there: two lines on two serial numbers pass
   when the location holds two units. Note that a line on a serial number that is not in
   the location also passes when the total is enough; that serial number then goes to -1
   and has to be corrected by an inventory adjustment.

   ![Done transfer from Raft Serii, Detailed Operations on SN-1001 and SN-1002](static/description/en/07_serie_check_debifat.png)

6. **Bring a negative position back to zero.** Once the cause is found and the missing
   documents are recorded, open *Inventory > Operations > Physical Inventory*, filter
   *Negative Stock*, enter the counted quantity (0 when the shelf is empty) and click
   **Apply**. An increase is an incoming move and is not blocked; a count that would take
   the stock below zero is blocked like any other outgoing move.

   ![Physical Inventory on a negative position: On Hand -5, Counted 0, Difference +5, before Apply](static/description/en/08_inventar_corectie_negativ.png)

Not checked: products without *Track Inventory*, non-internal locations, and Point of
Sale receipts while **Allow negative stock from Point of Sale** is enabled. Every Point of
Sale bypass is written to the server log with the transfer, product, quantity and
location.
