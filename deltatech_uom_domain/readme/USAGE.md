Install the module and enable **Units of Measure** in **Inventory → Configuration → Settings**. No
other configuration is needed: the unit lists are widened as soon as the module is installed.

1. **Choose any convertible unit on a purchase** — on a request for quotation, a purchase order or a
   vendor bill, the **Unit** list of a line offers every unit convertible to the product's unit (same
   reference unit), not only the packagings set on the product. A product in Units offers Dozens and
   any "10 Units" unit you created; it does not offer kg.
2. **Vendor pricelist lines** — on the product, **Purchase** tab, the unit of a vendor line can only be
   the product's unit, its packagings or a unit of the same tree. A unit from another tree (ml for a
   cable sold in meters) can no longer be chosen. Existing vendor lines are not changed.
3. **Set the default purchase unit** — on the product, **Purchase** tab, fill in **Default Purchase
   Unit** (only units convertible to the product's unit are offered). From then on:

   - a new vendor line takes this unit, and its unit can no longer be changed;
   - a purchase order line takes this unit when the product is chosen, even when the vendor line is
     missing or expired, and its unit can no longer be changed.

   Prices on vendor lines are expressed in the unit of the line: when you change the unit of an
   existing vendor line, correct its price as well.

Sales orders, customer invoices and stock moves keep the standard unit lists.
