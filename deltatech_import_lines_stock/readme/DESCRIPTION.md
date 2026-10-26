Loads stock moves and inventory counts from a file with the wizard of
`deltatech_import_lines`:

- **Transfers** (receipts, deliveries, internal transfers): an **Import
  Lines** button on transfers that are not done or cancelled. Each row
  becomes a move between the locations of the transfer. Moves added to a
  confirmed transfer are confirmed, and Odoo merges them with the
  existing moves of the same product.
- **Lots and serial numbers**: a **Lot/Serial Number** column sets the lot
  of the row. On receipts whose operation type allows new lots, a lot
  that does not exist is created at validation; on the other operations
  the lot must exist. A serial number row must have the quantity 1.
- **Inventory counts**: an **Import Counts** button on **Physical
  Inventory** sets the counted quantity of the products (and lots) in the
  chosen location. Rows of the same product and lot are added up. The
  count is applied by the user, with **Apply** or **Apply All**.

Installed automatically when both Inventory and `deltatech_import_lines`
are installed.
