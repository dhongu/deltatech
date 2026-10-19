1. Go to **Manufacturing > Products > Bills of Materials** and open the Bill of
   Materials of the product sold as a set.
2. Set **BoM Type** to **Kit** and tick **Restrict Incomplete Delivery** (the
   option is shown only for kits). Save.
3. Create and confirm a sales order for the kit product. The delivery order
   contains one line for each component.
4. On the delivery order, set the quantities of the components and click
   **Validate**:

   - if every component is present and the quantities follow the Bill of
     Materials ratio, the delivery is validated as usual;
   - if a component is missing, or its quantity breaks the ratio, Odoo shows
     a "Set delivery restriction" message and the delivery stays open.

5. Correct the quantities (or deliver fewer complete sets) and validate again.
