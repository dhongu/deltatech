The extra line is configured once, on the main product.

1. Create the **extra** product as an ordinary product, with the right price and
   taxes (for example a "Transport and handling" service).
2. Open the **main product** and go to the **Purchase** tab, group **Extra Line**:
   - **Extra Product** - the product that is added automatically;
   - **Extra Percent** - percentage of the main line's unit price. Leave **0** if
     the extra product has its own price (vendor price list or purchase price);
   - **Extra Quantity** - quantity multiplier (1 = one extra unit for every unit
     purchased).
3. Save.

Writing these fields requires write access on products (Purchase or Inventory
Manager). Daily use only requires **Purchase / User**.

The same fields are shown on the **Sales** tab when `deltatech_sale_add_extra_line`
is installed: the configuration is shared, so a configured product generates the
extra line on both sales and purchase orders.
