This module extends Odoo's internal product categories with two additional
grouping dimensions — **Category type** and **Category class** — enabling
businesses to segment and analyse inventory, sales margins, and invoices
at a finer level than the built-in category hierarchy.

**Key features:**

- Adds **Category type** and **Category class** fields to every product
  category (many2one relations to dedicated configuration lists).
- Configurable lists of types and classes, each with a drag-and-drop
  sequence, managed from the Inventory configuration menu.
- **Sale Margin report** (from `deltatech_sale_commission`) gains group-by
  filters for Category type and Category class.
- **Stock Quant** view gains search and group-by filters for both dimensions.
- **Account Invoice report** gains search and group-by filters for both
  dimensions.
- Access to the configuration lists is controlled by the dedicated security
  group **Manage category groups** (assigned to Administrator by default).
