Replenishment can add its lines to an existing draft purchase order of the vendor, including one a buyer is preparing by hand. This module marks the purchase orders that replenishment creates and stops replenishment from using any other order.

- **Replenishment flag**: Purchase orders created by a stock rule, for example from a reordering rule, get the `from_replenishment` flag set automatically.
- **Manual orders stay clean**: The search for an existing order to add lines to gets one more condition: the order must carry the flag. Orders without the flag are never used.
- **Replenishments still merge**: Successive replenishment needs of the same vendor still go into one flagged order, as the module's tests check.
- **Existing orders**: Orders created before the installation carry no flag, so replenishment does not add lines to them.
- **No screen**: The module adds no view, menu or setting, and the flag is not shown on the purchase order form.

The module depends on `purchase_stock` and has no access rules of its own. The flag is never cleared, so a flagged order stays open to replenishment even after a buyer adds lines by hand.
