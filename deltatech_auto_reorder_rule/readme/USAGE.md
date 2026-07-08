1. Mark the stock route(s) that should be used for auto-generated rules by enabling **Use this for auto rules** on the route (**Inventory > Configuration > Routes**).
2. Creating a new storable (`type='product'`) product automatically creates a matching reordering rule with default values.
3. For existing products, open a **Product Template** and use the **Create Rule** wizard: set the **Minimum Quantity**, **Maximum Quantity**, the **Stock Locations** to apply it to, and the **Trigger** (Automatic/Manual), then confirm to generate a `stock.warehouse.orderpoint` for each variant/location combination.
4. Rules are created only for storable products; the first route flagged for auto rules is used, if any.
