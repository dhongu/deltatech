This module works automatically in the background, with no configuration screen of its own:

1. Make sure the product has one or more **Packagings** defined (Inventory/Sales > product form > Packaging tab), each with a maximum quantity.
2. In a delivery or receipt (`stock.picking`), set the **Package** field on the move line to the desired product packaging.
3. When you click **Put in Pack**, the module automatically splits the move line into as many packages as needed so that no single package exceeds the maximum quantity declared on that packaging type. Any remaining quantity that doesn't fill a full package is placed in its own package.

No extra setup is required beyond defining the packaging's maximum quantity on the product.
