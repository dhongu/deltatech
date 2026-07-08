Go to **Inventory > Configuration > Operations Types**, open an operation type and,
under the sequence settings, configure any combination of:

- **Group for validation** — only users belonging to this security group can click
  **Validate** on transfers of this operation type; leave it empty to allow anyone.
- **Restrict done quantities to reserved** — when enabled, a transfer of this type
  cannot be validated if the done quantity of a line differs from the reserved
  quantity.
- **Restrict new products** — when enabled, a transfer of this type cannot be
  validated if a line has a done quantity but zero reserved quantity (i.e. a product
  that wasn't part of the original demand).

Users who don't meet these conditions get a blocking error when they try to validate
the picking.
