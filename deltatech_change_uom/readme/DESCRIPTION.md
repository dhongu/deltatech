A product created with the wrong unit of measure is often already used on orders, invoices and stock moves. This module adds a *Change Uom* action that replaces the unit on the product and those documents in one step.

- **Change Uom action**: The product form's action menu offers *Change Uom*. Its window shows the current *Unit of Measure* and *Default Purchase Unit*; *Apply* runs the change.
- **Unit choices**: *Unit of Measure* accepts any unit. *Default Purchase Unit* offers only units convertible to the new one and is cleared when a new unit does not fit it.
- **Documents updated**: For every variant, lines in the old unit move to the new one on sales orders, purchase orders, invoices, stock moves, stock move lines and vendor pricelists. Lines in the old purchase unit move to the new *Default Purchase Unit*, or to the new unit when it is empty.
- **No conversion**: Quantities, prices and amounts stay as they are. The update goes straight to the database, so posted invoices and locked periods do not stop it.

It depends on *Products*, *Invoicing*, *Inventory*, *Sales*, *Purchase* and *UoM Domain by Reference* (`deltatech_uom_domain`), which provides the *Default Purchase Unit*. Only users of the group *Allow to change unit of measure* (Settings administrators have it by default) can use the action.
