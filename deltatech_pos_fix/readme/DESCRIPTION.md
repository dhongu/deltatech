# Deltatech POS Fix

Fix POS total calculation when using tax-included fiscal position mapping.

When a product has a tax-included tax and a fiscal position maps it to a non-included tax (like 0% reverse charge), the POS should reduce the total price to the tax-excluded amount. This module patches the POS to handle this recalculation correctly, matching the backend Sales behavior.

This fix is applied both in the POS interface (JavaScript) and when generating invoices from POS orders (Python), ensuring consistency across the entire flow.

## Features

- Corrects unit price recalculation in POS when taxes change through the fiscal position.
- Ensures consistency between the Sales module and POS regarding the treatment of included taxes.
- Adapts the unit price on invoice lines generated from POS orders to reflect the correct tax mapping.
- Reconciles the invoice of a POS order paid in cash with change, when the POS receivable account is the
  customer's receivable account (4111 in the Romanian chart of accounts); without the fix the invoice stays unpaid.

## Installation

1. Copy the module into the addons folder.
2. Update the module list in Odoo.
3. Install the `deltatech_pos_fix` module.
