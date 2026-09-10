# Deltatech Stock Inventory

## Overview

The Deltatech Stock Inventory module restores and enhances the stock.inventory functionality in Odoo, providing
additional features for better inventory management and stock valuation control.

## Features

- **Legacy Inventory System**: Restores the functionality of the old stock.inventory model, which was removed in newer
  Odoo versions.
- **Enhanced Stock Valuation**:
  - Displays columns with the stock price in inventory views.
  - Allows updating product cost prices during inventory validation.
- **Valuation snapshot on the inventory line** (restricted to *Inventory / Administrator*):
  - **Unit Value** — the unit valuation cost snapshotted when the line is generated (stock value of
    the matching quants over their quantity, falling back to the product cost). It is refreshed by
    the *Refresh quantity* button and, unlike *Price*, it is never edited by the operator.
  - **Theoretical Value** / **Counted Value** / **Difference Value** — the value of the on hand
    quantity, of the counted quantity and of the difference, so the money impact of the count is
    visible **before** validation, not only after it.
  - **Posted Value** — the value actually posted by the inventory move of that line, filled in at
    validation. It can differ from the estimate for FIFO products, where the outgoing move is valued
    on the consumed layers.
  - The same four totals are summed on the inventory document, and the inventory move now carries an
    **Inventory Line** link, so a stock move can be traced back to the counted line.
- **Multi-Warehouse Stock Visibility**:
  - Displays stock broken down by warehouse codes directly in the product Kanban view.
  - Configuration option per warehouse to display total stock or only from the main location.
- **Manual Location Control**:
  - Adds fields for Rack, Row, Shelf, and Case on products and inventory lines.
  - Fields can be activated/deactivated from inventory settings.
- **Security Controls**:
  - Adds the "Can update quantities" security group to restrict who can modify inventory quantities.
- **Inventory Price Update**:
  - When the system parameter "stock.use_inventory_price" is set to True, the cost price of products (with FIFO evaluation)
    is updated with the price from the inventory lines.
- **Inventory Archiving**:
  - Option to archive old stock valuation layers (SVL) and create new ones based on inventory counts.
  - Supports compatibility with Romanian accounting modules (l10n_ro).
- **Barcode Support**:
  - Integrated barcode scanning functionality for faster inventory operations.
  - Supports scanning products and lot/serial numbers.
- **Enhanced Reporting**:
  - Built-in inventory reports.
  - Detailed views of inventory adjustments.
- **Inventory Management Functions**:
  - Filtering by location, rack, or product.
  - Marking inventory lines as "OK" for verification.
  - Creating new inventories from unverified lines.
  - Pre-filling counted quantities with current stock or zero.
  - Including exhausted products (with zero quantity).

## Configuration

- Set the system parameter "stock.use_inventory_price" to True to enable cost price updates during inventory.
- Enable "Show manual location fields" in Settings -> Inventory to use manual location fields.
- The "Can update quantities" security group must be assigned to users who need to update inventory quantities.

## Technical Details

The module implements:

- Complete reimplementation of the stock.inventory model.
- Integration with stock valuation layers (SVL) for proper accounting.
- Custom views for enhanced inventory operations.
- Barcode scanning capabilities for mobile inventory.
- Compatibility with Odoo 19 and Romanian accounting modules.
