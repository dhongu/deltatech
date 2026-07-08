1. Go to **Manufacturing > Products > Bills of Materials** and open (or create) the BoM for a product template.
2. Set the **Base Type** field on the BoM:
   - `Normal`: standard Odoo BoM, unaffected by this module.
   - `Base`: the master template that describes the general structure of components for the product template.
   - `Derived`: a variant-specific BoM generated from a `Base` BoM. Derived BoMs are automatically coded `D1`, `D2`, etc.
3. On a `Derived` BoM, use the **Recompute Components** button (in the header) to re-sync its lines from the `Base` BoM of the same product template — the module matches attributes to pick the correct component variant automatically.
4. On any BoM line, click the **Show** button (next to the component) to jump directly into the sub-BoM of that component, useful for multi-level structures.
5. When creating a **Manufacturing Order** and selecting a product variant, the module automatically creates (if missing) and computes the `Derived` BoM from the existing `Base` BoM.
6. While the Manufacturing Order is in draft, you can also press **Compute Derived BoM** in the header to manually (re)trigger this computation. The system recomputes the derived BoM again just before the order is confirmed, so component variants always match the latest attribute configuration.
