## Automatic rule creation

After the module is installed and configured (see CONFIGURE), every new storable product saved in the system will have a reorder rule created automatically for each warehouse that has **Generate Reorder Rules** enabled. No manual action is required.

## Bulk creation for existing products

1. Go to **Inventory > Products > Products** (or **Sales > Products > Products**).
2. Select one or more products in the list view.
3. Open the **Action** menu and click **Create rule**.
4. The system creates a reorder rule for each selected product that does not already have one, using the configured warehouse(s) and route.

## Creating rules with custom quantities (wizard)

1. Open a product form (**Inventory > Products > Products**, then click on a product).
2. Open the **Action** menu (gear icon) at the top of the form and click **Open Rules Wizard**.
3. In the dialog that opens, fill in:
   - **Minimum Quantity** — the quantity level that triggers replenishment.
   - **Maximum Quantity** — the quantity to replenish up to.
   - **Trigger** — choose *Automatic* (scheduler-driven) or *Manual*.
   - **Stock Locations** — select one or more internal locations for which to create rules.
4. Click **Create Rules**. A separate `stock.warehouse.orderpoint` record is created for each product variant and each selected location.

## Reviewing created rules

Go to **Inventory > Operations > Replenishment** to view and manage all reorder rules, including the ones created automatically by this module.
