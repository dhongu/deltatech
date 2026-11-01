Install the module together with its dependencies (`sale`, `website_sale`, `stock`). Then set up the products:

1. Create the **extra** product as a regular sellable product, with the correct sales price and taxes.
2. Open the **main** product and, on the **Sales** tab, fill in the **Extra Line** group:
   - **Extra Product**: the product that is added automatically;
   - **Extra Percent**: percentage of the main line price. Leave **0** if the extra product must be sold at its own price;
   - **Extra Quantity**: quantity multiplier (1 = one extra unit for each unit sold).
3. Make sure the user has the **Sales / User** access group.

For the Point of Sale, install the optional module `deltatech_sale_add_extra_line_pos`.
