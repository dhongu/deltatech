Install the module and enable **Units of Measure** in **Inventory → Configuration → Settings**. No
other configuration is needed: the unit lists are widened as soon as the module is installed. A new
unit joins a tree through its reference unit (for example "Cutie 100 buc", reference Units, ratio
100); it does not have to be added to each product.

1. **Set the default purchase unit** — on the product, **Purchase** tab, fill in **Default Purchase
   Unit** (1) with the unit you buy in. Only units convertible to the product's unit are offered. In
   the example, the beam is stocked per piece of 0.0384 m³ and has no vendor line.

   ![Purchase tab of the product Grindă molid 8x8 cm, 6 m: no vendor line, Default Purchase Unit (1) set to m³](static/description/en/01_produs_um_implicita_achizitie.png)

2. **The request for quotation takes it** — create a request for quotation (**Purchase → Orders →
   Requests for Quotation**, **New**) and add the product. The line is in **m³** even though the vendor
   has no pricelist line, and no other unit can be chosen. The proposed price is the cost converted
   to m³. On receipt, the 4.50 m³ enter the stock converted to pieces; without the module they would
   have entered as 4.50 pieces.

   ![Request for quotation to Gater Bistrița SRL: the line of Grindă molid 8x8 cm, 6 m is 4.50 in the highlighted unit m³, at 1,250.00, amount 5,625.00 lei](static/description/en/02_cerere_oferta_um_implicita.png)

3. **Choose any convertible unit** — for a product without a default purchase unit, the **Unit** list
   of a request for quotation, purchase order or vendor bill line offers every unit of the product's
   unit tree. A product in Units with no packaging offers Cutie 100 buc, Dozens, Pack of 6 and Units;
   it does not offer kg. Standard Odoo would offer only Units. Next to each unit, the list shows
   what the line quantity would mean in the product's unit (500 Cutie 100 buc = 50000 Units):
   changing the unit does not recalculate the quantity, so correct both together.

   ![Request for quotation to Feronerie Nord SRL: the Unit list of the Șurub autoforant 4,2x13 line shows Cutie 100 buc, Dozens, Pack of 6 and Units](static/description/en/03_cerere_oferta_lista_um.png)

4. **Vendor lines** — on the product, **Purchase** tab, the unit of a vendor line can only be the
   product's unit or a unit of the same tree. A unit from another tree (ml for a cable sold in meters)
   can no longer be chosen. When the product has a default purchase unit, a new vendor line takes it
   and its unit cannot be changed. Existing vendor lines are not changed: when you correct their unit,
   correct their price as well, since the price is expressed in the unit of the line.

   ![Purchase tab of the product Șurub autoforant 4,2x13: the Unit list of the Feronerie Nord SRL vendor line shows Units, Pack of 6, Dozens and Cutie 100 buc](static/description/en/04_furnizor_lista_um.png)

Sales orders, customer invoices and stock moves keep the standard unit lists: customer invoices are
sent with the UNECE code of the unit, and a unit without a mapped code would be declared as a piece.
