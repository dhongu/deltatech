# Deltatech POS Fix

This module solves an issue in the Point of Sale (POS) related to the total calculation when using a fiscal position
that maps a tax-included tax to a 0% tax (reverse charge).

Fix POS total calculation when using tax-included fiscal position mapping.

When a product has a tax-included tax and a fiscal position maps it to a non-included tax (like 0% reverse charge), the
POS should reduce the total price to the tax-excluded amount. This module patches the POS to handle this recalculation
correctly, matching the backend Sales behavior.

## Features

- Corrects the unit price recalculation in POS when taxes change through the fiscal position.
- Ensures consistency between the Sales module and POS regarding the treatment of included taxes.

## Installation

1. Copy the module into the addons folder.
2. Update the module list in Odoo.
3. Install the `deltatech_pos_fix` module.

## Configuration

No additional configuration is required. The module automatically extends the tax calculation logic in POS.
