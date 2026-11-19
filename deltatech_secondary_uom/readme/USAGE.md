## Define the conversions on the product

Open the product (**Inventory → Products → Products**) and go to the **Alternative Units** tab.
Each line says how many alternative units correspond to how many base units, for example
**3 m² = 4 Units** for a tile kept in pieces, or **15 kg = 1 Units**. The **Base Unit** column is the
product unit, filled in automatically. A product has at most one conversion per alternative unit,
and the alternative unit must differ from the base unit.

![Alternative Units tab of a tile kept in Units, with the lines 3 m² = 4 Units and 15 kg = 1 Units](static/description/en/01_produs_gresie_unitati_alternative.png)

A product kept in a continuous unit works the same way: an aluminium profile kept in **m** has the
line **1 Bar = 5.8 m**. A unit that does not exist yet (such as **Bar**) is created first in
**Inventory → Configuration → Products → Units & Packagings**. A counting unit that will be the
base unit of products (Bag, Roll, Box) must be created with the **Units** reference, otherwise it is
treated as a continuous unit and quantities are not rounded up to whole pieces.

![Alternative Units tab of a profile kept in m, with the line 1 Bar = 5.8 m](static/description/en/02_produs_profil_bara.png)

## Enter the quantity in the secondary unit

On a quotation (**Sales → Orders → Quotations**), show the **Secondary Quantity** and
**Secondary Unit** columns from the optional columns menu of the order lines (they are hidden by
default). On each line, choose the **Secondary Unit** among the product conversions, type the
**Secondary Quantity** and save: the line **Quantity** is computed in the base unit when the order
is saved.

- For a product kept in pieces, the quantity is rounded **up** to whole pieces: 40 m² of tiles give
  54 Units, and the secondary quantity is realigned to 40.50 m².
- For a product kept in a continuous unit (m, kg, m²), the exact quantity is kept: 3 bars of 5.8 m
  give 17.40 m.

The unit price and the amounts stay in the base unit.

![Sales order with the Secondary Quantity and Secondary Unit columns: tiles 40.50 m² for 54.00 Units, profile 3.00 Bar for 17.40 m](static/description/en/03_comanda_vanzare_unitate_secundara.png)

## Deliveries and receipts

The secondary unit follows the order on the delivery or the receipt. On the **Operations** tab of
the transfer, the same two optional columns show the secondary quantity computed from the move
quantity.

![Delivery of the order, Operations tab with the secondary quantity of each move](static/description/en/04_livrare_unitate_secundara.png)

Purchase order lines work the same way: 150 kg of tiles give 10.00 Units.

![Request for quotation with the tiles entered in kg: 150.00 in Secondary Quantity and 10.00 Units in Quantity](static/description/en/05_comanda_achizitie_unitate_secundara.png)
