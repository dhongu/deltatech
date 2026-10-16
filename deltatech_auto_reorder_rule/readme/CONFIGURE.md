## Warehouse configuration

Go to **Inventory > Configuration > Warehouses**, open the warehouse form, and look for the **Generate Reorder Rules** checkbox (added by this module in the replenishment section). Enable it on every warehouse for which rules should be created automatically. It is enabled by default on new warehouses.

## Route configuration

Go to **Inventory > Configuration > Routes**, open the route you want to use for auto-created rules, and enable the **Use This for Auto Rules** flag. Only one route should have this flag active at a time; if none is set, rules are created without a route.

## Disabling automatic creation on product save

By default, a reorder rule is created every time a new storable product is saved. To disable this behaviour without uninstalling the module, go to **Settings > Technical > System Parameters** and set:

- **Key**: `deltatech_auto_reorder_rule.dont_auto_create_rule`
- **Value**: `True`

When this parameter is set, rules are no longer created on product creation but can still be generated manually via the server actions on the Products list or form.
