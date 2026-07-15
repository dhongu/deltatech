Features:

- You can set a minimum quantity and a multiple quantity on the product.
- Rules are configured in the product's default unit of measure and converted to the sale line unit.
- If you try to sell less than the minimum, the quantity is raised to the first valid multiple at or above that minimum.
- A multiple of 0 or 1 disables the multiple restriction; a minimum of 0 disables the minimum restriction.
- Rules are enforced consistently in form onchanges, imports, ORM creates, and single or batch writes.
