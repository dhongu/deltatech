Labor, utilities and overhead are production costs that components do not show. This module records them on the bill of materials and the manufacturing order and adds them to the order cost.

- **Costs tab**: A *Costs* tab on the bill of materials and the manufacturing order holds *Overhead*, *Utility consumption*, *Net Salary Rate*, *Salary Contributions* and a *Duration*. A new order copies *Overhead*, *Utility consumption*, *Net Salary Rate* and *Salary Contributions* from its bill of materials.
- **Order cost**: *Overhead* is a fixed amount; utilities, net salary and contributions are rates multiplied by the *Duration*. *Production Amount* and *Calculate Price* show the total and unit cost: storable components at standard price plus these costs, or, once produced, the stock valuation of the finished moves.
- **Finished product cost**: Before Odoo prices the finished product, the module sets the order's `extra_cost` to the costs divided by the order quantity, when they are not zero, then runs the standard calculation.
- **Printed order**: The production order report adds the start date, the non-zero cost values, a *Finished Products* table, and *Effective Quantity*, *Price* and *Amount* columns on the components.

It depends on `mrp_account`. Later changes to a bill of materials do not reach existing orders, and costs typed on a new order are replaced by those of its bill of materials at the first save.
