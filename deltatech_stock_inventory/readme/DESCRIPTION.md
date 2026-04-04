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
