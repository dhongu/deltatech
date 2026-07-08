1. From a **Product Template**, **Product Variant**, **Sale Order**,
   **Transfer** (stock.picking), **Lot/Serial Number**, or **Stock
   Quant**, select one or more records and use the **Print > Product
   Labels** action. By default this module overrides the standard
   "Print Labels" button on products with its own wizard.
2. In the wizard, choose the **Layout** (the report to use — custom
   layouts can be created by defining a new report on the
   `product.product.label` model), optionally a **Warehouse**,
   **Price List** and a **Location** (enable **Use ptw rules** to
   restrict to a specific location).
3. Enable **Print lots only** to generate one label per lot/serial
   number currently in stock for the selected products instead of one
   label per product.
4. When printing labels from a transfer that creates lots/serials on
   receipt, you can enable **Auto-generate lots** to have the system
   assign lot numbers automatically before printing.
5. Review/edit the generated label lines (product, quantity, lot,
   price) in the wizard's table, then click **Print**.
6. To stop the module from overriding the standard print button, set
   the system parameter `terrabit_labels.override_print_button` to
   `False` (Settings > Technical > System Parameters, developer mode).
