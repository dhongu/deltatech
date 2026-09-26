Manage multiple alternative codes per product and find any item by any of its codes.
This module is useful when the same product is known under different references — supplier
codes, manufacturer part numbers, legacy codes, or customer-specific identifiers — and your
team needs to locate it regardless of which code they have at hand.

**Key features:**

- Adds a dedicated **Alternative** tab on the product form where you can record any number
  of extra codes, reorder them, and optionally hide individual codes from the combined
  display.
- Exposes a computed **Alternative Code** field (visible in the product list and on
  documents) that concatenates all visible codes for quick reference.
- Extends product search so that typing an alternative code returns the matching product,
  on both product templates and their variants. The search is opt-in and tunable from
  Settings.
- Surfaces the alternative code column on **Sales Order**, **Purchase Order**, and
  **Stock Move** lines, keeping the code visible throughout the order-to-delivery flow.
- Adds a free-text **Used For** field on the product to note what the item can be used for,
  aiding identification and cross-selling.
- A daily scheduled action splits codes entered on one line and separated by `;` or `,`
  into one alternative record per code, without creating codes the product already has.
  Spaces are kept as part of the code (OEM numbers such as `366 200 05 01`).
