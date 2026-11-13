Labor, utilities and overhead are costs that components do not show. This module records them on the bill of materials and the manufacturing order and adds them to the order cost.

- **Costs tab**: A *Costs* tab on the bill of materials and the manufacturing order holds *Overhead*, *Utility consumption*, *Net Salary Rate*, *Salary Contributions* and a duration. On the order, the tab shows the standard `duration` field, not the `duration_cost` field that the cost formulas read.
- **New orders**: A new order copies the four cost values from its bill of materials and sets `duration_cost` to the *Duration* of the bill, scaled to the order quantity.
- **Order cost**: *Overhead* is a fixed amount; utilities, net salary and contributions are rates multiplied by `duration_cost`. *Production Amount* and *Calculate Price* show the total and unit cost: storable components at standard price plus these costs, or, once produced, the value of the finished moves.
- **Finished product cost**: Before Odoo prices the finished product, the module sets `extra_cost` to the costs divided by the order quantity, when they are not zero.
- **Printed order**: The production order report adds the start date, the non-zero cost values, a *Finished Products* table, and cost columns on the components.

It depends on `mrp_account`. Later bill changes do not reach existing orders.
