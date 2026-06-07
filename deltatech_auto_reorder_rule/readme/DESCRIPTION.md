Automatically creates reorder rules (replenishment rules) for products in Odoo, reducing the manual overhead of setting up stock replenishment in warehouses that manage many SKUs.

**Key features:**

- Automatically creates a `stock.warehouse.orderpoint` entry for every new storable product, using the warehouse and route marked for auto-rules.
- Provides a **Create rule** server action (available on the Products list) to generate rules in bulk for existing products that do not yet have one.
- Provides an **Open Rules Wizard** server action (available on the product form) to create rules for specific locations, with configurable minimum/maximum quantities and trigger mode (automatic or manual).
- A system parameter allows disabling the automatic rule creation on product creation, without uninstalling the module.
- Rules are only created for warehouses that have the **Generate Reorder Rules** option enabled, ensuring multi-warehouse setups can opt in or out per warehouse.
- A dedicated flag on stock routes (**Use This for Auto Rules**) controls which route is assigned to automatically created rules.
