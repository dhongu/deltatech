Features:
 - Adds the old stock.inventory model, with its functionalities
 - Display stock price column at inventory
 - Security group "Can update quantities" is added. Only users in this group can update product quantities

If system parameter "stock.use_inventory_price" is set to True, the cost price of the product is updated with the price on the inventory line (only if product has FIFO evaluation), so the stock valuation that is generated from the inventory has the line's unit price
