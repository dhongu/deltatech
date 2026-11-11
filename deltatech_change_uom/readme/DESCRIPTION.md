A product created with the wrong unit of measure is often already used on orders, invoices and stock moves. This module adds a *Change Uom* action that replaces the unit on the product and those documents in one step.

- **Change Uom action**: The product form's action menu offers *Change Uom*. Its window shows the current *Unit of Measure* and *Purchase Unit of Measure*; *Apply* runs the change.
- **Unit choices**: *Unit of Measure* accepts any unit, and choosing one sets *Purchase Unit of Measure* to the same unit. A purchase unit outside the category of the *Unit of Measure* is replaced by that unit.
- **Documents updated**: For every variant, lines in the old unit move to the new one on sales orders, invoices, stock moves and stock move lines. Purchase order lines in the old purchase unit move to the new *Purchase Unit of Measure*.
- **No conversion**: Quantities, prices and amounts stay as they are. The update goes straight to the database, so posted invoices and locked periods do not stop it.

It depends on *Products*, *Invoicing*, *Inventory*, *Sales* and *Purchase*. Any internal user who can open the product form can use the action.
