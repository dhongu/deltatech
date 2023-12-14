Features:
 - Adds the old stock.inventory model, with its functionalities
 - Display stock price column at inventory
 - Security group "Can update quantities" is added. Only users in this group can update product quantities
 - Option to archive old SVL's added
 - Functions to create putaway rule and move product to it's location
 - System parameter stock.use_inventory_price - if set to True, the cost price of the product is updated with the price on the inventory line (only if product has FIFO evaluation), so the stock valuation that is generated from the inventory has the line's unit price
 - System parameter inventory.can_archive_svl - if set to True, the option to archive old SVL's is activated in the inventory. This option archive all SVLs of the inventoried products, so only the SVLs created by the inventory will be visible.
