

Ensures data integrity by blocking the confirmation of Sales Orders that do not contain any actual product lines. This helps prevent accidental confirmations of orders that only include delivery charges, discounts, or otherwise lack real products.

- Features:
  - Prevents confirming a sales order without product lines
  - Works seamlessly with the standard Sales Order confirmation flow
  - Provides clear user feedback when confirmation is not allowed
  - Zero configuration; lightweight and safe to adopt

- Usage:
  - Install the module and use Sales Orders as usual
  - If an order has no real product lines, the confirmation action will be blocked with an explanatory message

- Compatibility:
  - Designed to work with standard Odoo Sales workflows
