Enable **Units of Measure** in *Inventory → Configuration → Settings* and
create the alternative unit (e.g. **Bar**) in *Inventory → Configuration →
Units & Packagings*, without a reference unit: its factor is set on each
product, not on the unit.

1. Open the product (*Inventory → Products → Products*), tab **Alternative
   Units**, and add a line: **Alternative Quantity** 1, **Alternative Unit**
   Bar, **Base Quantity** 6. It reads "1 Bar = 6 m"; **Base Unit** shows the
   product unit.

   ![Alternative Units tab of the product Profil aluminiu 40x40: one line with Alternative Quantity 1, Alternative Unit Bar, Base Quantity 6 and Base Unit m](static/description/en/01_produs_unitati_alternative.png)

2. The same unit can have another factor on another product: on the stainless
   pipe, 1 Bar = 5 m.

   ![Alternative Units tab of the product Țeavă inox 25 mm: one line with Alternative Quantity 1, Alternative Unit Bar, Base Quantity 5 and Base Unit m](static/description/en/02_produs_b_unitati_alternative.png)

3. On a sale order line, choose **Secondary Unit** Bar and type 10 in
   **Secondary Quantity**: the line quantity becomes 60 m. Both columns are
   hidden by default; show them from the optional columns button of the lines
   list. The unit price stays per metre.

   ![Sale order to Construct Vest SRL: the Profil aluminiu 40x40 line with Secondary Quantity 10 and Secondary Unit Bar, quantity 60 in m and the price per metre](static/description/en/03_comanda_vanzare_bare.png)

4. On a purchase order line, 8 Bar of pipe give 40 m. The price is per metre:
   a vendor price of 100 per 5 m bar is entered as 20 per metre.

   ![Purchase order to Metal Profil SRL: the Țeavă inox 25 mm line with Secondary Quantity 8 and Secondary Unit Bar, quantity 40 in m and unit price 20 per metre](static/description/en/04_comanda_achizitie_bare.png)

5. The receipt (and the delivery of a sale order) keeps the secondary unit of
   the order line. The secondary quantity of the move is computed from the
   **Demand**; the quantity actually received is entered in the **Quantity**
   column, in the base unit. Do not edit the secondary quantity on a receipt:
   it changes the demand, not the received quantity.

   ![Receipt of the purchase order: the Țeavă inox 25 mm move with Secondary Quantity 8 and Secondary Unit Bar, demand 40 m](static/description/en/05_receptie_bare.png)

Stock, prices, invoices and stock valuation stay in the product base unit. See
*Use Cases / Context* for the limitations and for the standard alternative
(one real unit per factor) when the price, the receipt or the bill of
materials must be in bars.
